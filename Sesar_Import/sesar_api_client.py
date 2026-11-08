"""
sesar_api_client.py
-------------------
Python client for the SESAR REST API (https://docs.geosamples.org/api/).

Replaces the old ad-hoc ``requests.get("https://app.geosamples.org/sample/igsn/...")``
calls scattered through the UI files. Everything that talks to SESAR goes
through ``SesarApiClient`` so authentication, token refresh, error handling,
and logging live in one place.

Endpoints used
    GET    samples/                 search / list   (token optional)
    GET    samples/{igsn}/          fetch one       (token optional for published)
    PATCH  samples/{igsn}/          update          (token + edit permission)
    POST   samples/                 register        (token)
    POST   auth/token/refresh/      rotate tokens   (no auth header)
    GET    users/me/                connection test (token)

Environments
    "sandbox"     https://api-sandbox.geosamples.org/api/   (default)
    "production"  https://api.geosamples.org/api/
    Selected in Settings → SESAR; stored as QSettings key ``sesar_environment``.
    Each environment keeps its own token pair.

Tokens
    Access tokens last 1 day, refresh tokens 1 year and ROTATE on every use
    (the old refresh token is revoked immediately). The client therefore
    always persists the new pair returned by the refresh endpoint before
    retrying the original request. Tokens are stored in the OS keyring via
    the ``keyring`` package when available, else in GeoCORK's QSettings.
    Token values are never written to any log.

Thread safety
    A client instance may be used from QThread workers (requests is
    thread-safe per Session for our usage). Token refresh is serialized with
    a lock so two workers hitting a 401 at once don't both spend the same
    (single-use) refresh token.
"""

from __future__ import annotations

import base64
import json
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter

try:  # urllib3 ships with requests
    from urllib3.util.retry import Retry
except Exception:  # pragma: no cover
    Retry = None

from Sesar_Import.sesar_logger import get_sesar_logger


# ===========================================================================
# Configuration
# ===========================================================================

ENVIRONMENTS: Dict[str, str] = {
    "sandbox":    "https://api-sandbox.geosamples.org/api/",
    "production": "https://api.geosamples.org/api/",
}
DEFAULT_ENVIRONMENT = "sandbox"

# Web app pages where users generate tokens (Developer Settings).
DEVELOPER_SETTINGS_URLS: Dict[str, str] = {
    "sandbox":    "https://app-sandbox.geosamples.org/profile/developer-settings",
    "production": "https://app.geosamples.org/profile/developer-settings",
}

# Public landing page for a sample, used for "Open in browser".
LANDING_PAGE_URL = "https://doi.org/{igsn}"

# QSettings keys (no token values live here unless keyring is unavailable).
SETTING_ENVIRONMENT = "sesar_environment"
SETTING_SESAR_CODE = "sesar_code"
SETTING_DEFAULT_OBJECT_TYPE = "sesar_default_object_type"
DEFAULT_OBJECT_TYPE = "Individual sample"

KEYRING_SERVICE = "GeoCORK-SESAR"
TOKEN_KINDS = ("access", "refresh")

DEFAULT_TIMEOUT = (10, 60)     # (connect, read) seconds
REFRESH_SKEW_SECONDS = 120     # refresh proactively when < 2 min remain
MAX_PAGE_SIZE = 2000

# Fields the API refuses to change via PATCH.
PATCH_FORBIDDEN_FIELDS = frozenset({"igsn", "sesar_code", "team", "registration_date"})
# Lists that PATCH replaces wholesale (sending them overwrites remote values).
PATCH_REPLACED_LISTS = frozenset({"other_names", "material_types", "collectors",
                                  "related_resources"})


def _get_qsettings():
    """GeoCORK's shared QSettings object (imported lazily for testability)."""
    from Functions.Settings_manager import SettingsManager
    return SettingsManager().settings


def current_environment(settings=None) -> str:
    settings = settings if settings is not None else _get_qsettings()
    env = str(settings.value(SETTING_ENVIRONMENT, DEFAULT_ENVIRONMENT) or DEFAULT_ENVIRONMENT)
    return env if env in ENVIRONMENTS else DEFAULT_ENVIRONMENT


def configured_sesar_code(settings=None) -> str:
    settings = settings if settings is not None else _get_qsettings()
    return str(settings.value(SETTING_SESAR_CODE, "") or "").strip()


def configured_default_object_type(settings=None) -> str:
    settings = settings if settings is not None else _get_qsettings()
    return str(settings.value(SETTING_DEFAULT_OBJECT_TYPE, DEFAULT_OBJECT_TYPE)
               or DEFAULT_OBJECT_TYPE).strip()


# ===========================================================================
# IGSN helpers
# ===========================================================================

_IGSN_WRAPPER_RE = re.compile(
    r"^(?:https?://(?:dx\.)?doi\.org/|https?://igsn\.org/|doi:|igsn:)\s*",
    re.IGNORECASE,
)
_DOI_PREFIX_RE = re.compile(r"^10\.\d{4,9}/")


def normalize_igsn(raw: Optional[str]) -> str:
    """
    Clean up a user-entered IGSN while KEEPING the DOI prefix.

    The new API addresses samples as ``samples/10.58052/XXXX/``; the prefix
    is part of the identifier. We only strip wrappers people paste in:

        "https://doi.org/10.58052/TAP00002Y" -> "10.58052/TAP00002Y"
        "IGSN: 10.58052/TAP00002Y"           -> "10.58052/TAP00002Y"
        " TAP00002Y "                        -> "TAP00002Y"  (bare; resolved by fetch)
    """
    s = (raw or "").strip()
    s = _IGSN_WRAPPER_RE.sub("", s).strip().strip("/")
    return s


def has_doi_prefix(igsn: str) -> bool:
    return bool(_DOI_PREFIX_RE.match(igsn or ""))


def bare_igsn(igsn: str) -> str:
    """'10.58052/TAP00002Y' -> 'TAP00002Y' (for comparisons only)."""
    return _DOI_PREFIX_RE.sub("", normalize_igsn(igsn))


def igsn_path(igsn: str) -> str:
    """URL path segment for an IGSN; the DOI slash stays a real path separator."""
    return quote(normalize_igsn(igsn), safe="/")


# ===========================================================================
# JWT helpers (no signature verification — only reading `exp` for scheduling)
# ===========================================================================

def jwt_expiry(token: Optional[str]) -> Optional[float]:
    """Return the token's `exp` claim (epoch seconds) or None if unreadable."""
    if not token or token.count(".") != 2:
        return None
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode("ascii")))
        exp = payload.get("exp")
        return float(exp) if exp is not None else None
    except Exception:
        return None


def describe_token(token: Optional[str]) -> str:
    """Human-readable status for the Settings UI."""
    if not token:
        return "not set"
    exp = jwt_expiry(token)
    if exp is None:
        return "set (expiry unknown)"
    remaining = exp - time.time()
    when = time.strftime("%Y-%m-%d %H:%M", time.localtime(exp))
    if remaining <= 0:
        return f"expired {when}"
    if remaining < 3600:
        return f"valid, expires in {int(remaining // 60)} min ({when})"
    if remaining < 86400 * 2:
        return f"valid, expires in {remaining / 3600:.1f} h ({when})"
    return f"valid until {when}"


# ===========================================================================
# Token storage
# ===========================================================================

class TokenStore:
    """
    Stores the access/refresh token pair per environment.

    Prefers the OS keyring (Windows Credential Manager, macOS Keychain,
    Secret Service on Linux). If ``keyring`` isn't installed, or only a
    "fail"/null backend is available, falls back to QSettings under
    ``sesar/<env>/<kind>_token`` (plaintext on disk — the Settings tab tells
    the user which backend is active).
    """

    def __init__(self, settings=None, use_keyring: Optional[bool] = None):
        self._settings = settings
        self._keyring = None
        if use_keyring is not False:
            self._keyring = self._load_keyring()
        self._lock = threading.RLock()

    # -- backend detection -------------------------------------------------
    @staticmethod
    def _load_keyring():
        try:
            import keyring
            from keyring.backends import fail
            backend = keyring.get_keyring()
            if isinstance(backend, fail.Keyring):
                return None
            # The "null" backend silently drops everything — treat as absent.
            if type(backend).__module__.endswith(".null"):
                return None
            return keyring
        except Exception:
            return None

    @property
    def backend_name(self) -> str:
        if self._keyring is not None:
            try:
                return f"OS keyring ({type(self._keyring.get_keyring()).__name__})"
            except Exception:
                return "OS keyring"
        return "GeoCORK settings file (plaintext — install 'keyring' for secure storage)"

    @property
    def settings(self):
        if self._settings is None:
            self._settings = _get_qsettings()
        return self._settings

    @staticmethod
    def _key(env: str, kind: str) -> str:
        if kind not in TOKEN_KINDS:
            raise ValueError(f"unknown token kind {kind!r}")
        return f"{env}:{kind}"

    # -- API ---------------------------------------------------------------
    def get(self, env: str, kind: str) -> Optional[str]:
        key = self._key(env, kind)
        with self._lock:
            if self._keyring is not None:
                try:
                    val = self._keyring.get_password(KEYRING_SERVICE, key)
                    if val:
                        return val
                except Exception as exc:
                    get_sesar_logger().warning(f"Keyring read failed ({kind}, {env}): {exc}")
            val = self.settings.value(f"sesar/{env}/{kind}_token", "")
            return str(val) if val else None

    def set(self, env: str, kind: str, value: Optional[str]) -> None:
        key = self._key(env, kind)
        value = (value or "").strip()
        with self._lock:
            if not value:
                self.clear(env, kind)
                return
            if self._keyring is not None:
                try:
                    self._keyring.set_password(KEYRING_SERVICE, key, value)
                    # Make sure no stale plaintext copy lingers.
                    self.settings.remove(f"sesar/{env}/{kind}_token")
                    return
                except Exception as exc:
                    get_sesar_logger().warning(
                        f"Keyring write failed ({kind}, {env}); using settings file: {exc}")
            self.settings.setValue(f"sesar/{env}/{kind}_token", value)

    def set_pair(self, env: str, access: Optional[str], refresh: Optional[str]) -> None:
        with self._lock:
            if access is not None:
                self.set(env, "access", access)
            if refresh is not None:
                self.set(env, "refresh", refresh)

    def clear(self, env: str, kind: Optional[str] = None) -> None:
        kinds = TOKEN_KINDS if kind is None else (kind,)
        with self._lock:
            for k in kinds:
                if self._keyring is not None:
                    try:
                        self._keyring.delete_password(KEYRING_SERVICE, self._key(env, k))
                    except Exception:
                        pass  # not present
                self.settings.remove(f"sesar/{env}/{k}_token")


class MemoryTokenStore(TokenStore):
    """In-memory store (tests, or ad-hoc tokens that shouldn't be persisted)."""

    def __init__(self, tokens: Optional[Dict[str, str]] = None):
        self._mem: Dict[str, str] = dict(tokens or {})
        self._lock = threading.RLock()
        self._keyring = None
        self._settings = None

    @property
    def backend_name(self) -> str:
        return "memory"

    def get(self, env, kind):
        return self._mem.get(self._key(env, kind))

    def set(self, env, kind, value):
        value = (value or "").strip()
        if value:
            self._mem[self._key(env, kind)] = value
        else:
            self._mem.pop(self._key(env, kind), None)

    def clear(self, env, kind=None):
        for k in (TOKEN_KINDS if kind is None else (kind,)):
            self._mem.pop(self._key(env, k), None)


# ===========================================================================
# Errors
# ===========================================================================

class SesarApiError(Exception):
    """Base error. `status` is the HTTP status (None for network failures)."""

    def __init__(self, message: str, status: Optional[int] = None,
                 errors: Any = None, url: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.errors = errors
        self.url = url

    def details(self) -> str:
        """Multi-line description suitable for a QMessageBox."""
        parts = [self.message]
        if self.status is not None:
            parts.append(f"HTTP {self.status}")
        if self.errors:
            parts.append(_format_field_errors(self.errors))
        if self.url:
            parts.append(f"URL: {self.url}")
        return "\n\n".join(p for p in parts if p)


class SesarConnectionError(SesarApiError):
    pass


class SesarAuthError(SesarApiError):
    """401 that refreshing couldn't fix, or no token configured."""


class SesarPermissionError(SesarApiError):
    """403 — authenticated but not allowed (e.g. no edit permission)."""


class SesarNotFoundError(SesarApiError):
    pass


class SesarValidationError(SesarApiError):
    """400 — field-level problems are in `.errors` (dict field -> messages)."""


def _format_field_errors(errors: Any) -> str:
    if isinstance(errors, dict):
        lines = []
        for k, v in errors.items():
            if isinstance(v, (list, tuple)):
                v = "; ".join(str(x) for x in v)
            elif isinstance(v, dict):
                v = _format_field_errors(v)
            lines.append(f"• {k}: {v}")
        return "\n".join(lines)
    if isinstance(errors, (list, tuple)):
        return "\n".join(f"• {e}" for e in errors)
    return str(errors)


# ===========================================================================
# Results
# ===========================================================================

@dataclass
class SearchPage:
    items: List[Dict[str, Any]]
    count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    raw: Dict[str, Any] = field(default_factory=dict, repr=False)


def _parse_search_envelope(body: Any, page: int, page_size: int) -> SearchPage:
    """
    The docs describe the list response two ways; accept both:

      A) {"count", "next", "previous", "results": [ {"count", "data": [..],
           "current_page", "total_pages", ...} ]}         (OpenAPI schema)
      B) {"count", "next", "previous", "current_page", "total_pages",
           "data": [..]}                                    (guide page)

    Plus a plain list, just in case.
    """
    if isinstance(body, list):
        return SearchPage(body, len(body), page, page_size, 1, False, page > 1, {})
    if not isinstance(body, dict):
        raise SesarApiError("Unexpected search response format.")

    items: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = body
    results = body.get("results")
    if isinstance(results, list):
        for chunk in results:
            if isinstance(chunk, dict) and isinstance(chunk.get("data"), list):
                items.extend(x for x in chunk["data"] if isinstance(x, dict))
                meta = {**body, **{k: v for k, v in chunk.items() if k != "data"}}
            elif isinstance(chunk, dict):
                items.append(chunk)
    elif isinstance(body.get("data"), list):
        items = [x for x in body["data"] if isinstance(x, dict)]

    count = int(meta.get("count") or body.get("count") or len(items))
    cur = int(meta.get("current_page") or page)
    size = int(meta.get("page_size") or page_size)
    total = meta.get("total_pages")
    total = int(total) if total else max(1, -(-count // max(size, 1)))
    has_next = bool(meta.get("next") or body.get("next")) or cur < total
    has_prev = bool(meta.get("previous") or body.get("previous")) or cur > 1
    return SearchPage(items, count, cur, size, total, has_next, has_prev, body)


def unwrap_sample(body: Any) -> Dict[str, Any]:
    """
    Return the flat sample dict from a detail/create/update response.

    The new API returns the object itself. Defensive unwrapping covers a
    `{"data": {...}}` envelope and the legacy `{"sample": {...}}` shape.
    """
    if isinstance(body, dict):
        for key in ("data", "sample"):
            inner = body.get(key)
            if isinstance(inner, dict) and ("igsn" in inner or "name" in inner):
                return inner
        return body
    raise SesarApiError("Unexpected sample response format.")


# ===========================================================================
# Client
# ===========================================================================

class SesarApiClient:
    """
    Usage:
        client = SesarApiClient.from_settings()
        page = client.search(q="basalt", page_size=50)
        sample = client.get_sample("10.58052/IEXXX0001")
        client.update_sample(igsn, {"location_description": "Outcrop"})
        new = client.register_sample({"name": "...", "object_type": "...",
                                      "latitude": 41.5, "longitude": -72.8})
    """

    def __init__(self, environment: str = DEFAULT_ENVIRONMENT,
                 token_store: Optional[TokenStore] = None,
                 base_url: Optional[str] = None,
                 session: Optional[requests.Session] = None,
                 timeout=DEFAULT_TIMEOUT,
                 user_agent: str = "GeoCORK SESAR client"):
        if environment not in ENVIRONMENTS and base_url is None:
            raise ValueError(f"Unknown SESAR environment {environment!r}")
        self.environment = environment
        self.base_url = (base_url or ENVIRONMENTS[environment]).rstrip("/") + "/"
        self.tokens = token_store if token_store is not None else TokenStore()
        self.timeout = timeout
        self._refresh_lock = threading.Lock()
        self.session = session or self._build_session()
        self.session.headers.update({"Accept": "application/json",
                                     "User-Agent": user_agent})

    @classmethod
    def from_settings(cls, settings=None, **kwargs) -> "SesarApiClient":
        settings = settings if settings is not None else _get_qsettings()
        return cls(environment=current_environment(settings),
                   token_store=kwargs.pop("token_store", None) or TokenStore(settings),
                   **kwargs)

    @staticmethod
    def _build_session() -> requests.Session:
        s = requests.Session()
        if Retry is not None:
            # Retry idempotent requests only on transient server errors /
            # rate limiting. POST/PATCH are never retried automatically.
            retry = Retry(total=3, backoff_factor=0.8,
                          status_forcelist=(429, 502, 503, 504),
                          allowed_methods=frozenset({"GET"}),
                          respect_retry_after_header=True,
                          raise_on_status=False)
            s.mount("https://", HTTPAdapter(max_retries=retry))
        return s

    # -- token helpers -----------------------------------------------------
    @property
    def access_token(self) -> Optional[str]:
        return self.tokens.get(self.environment, "access")

    @property
    def refresh_token(self) -> Optional[str]:
        return self.tokens.get(self.environment, "refresh")

    def has_credentials(self) -> bool:
        return bool(self.access_token or self.refresh_token)

    def refresh_tokens(self) -> str:
        """
        Exchange the refresh token for a new pair and persist BOTH.

        Serialized with a lock: refresh tokens are single-use, so if another
        thread already refreshed while we waited, reuse its new access token.
        """
        before = self.access_token
        with self._refresh_lock:
            current = self.access_token
            if current and current != before:
                return current  # someone else refreshed while we waited
            refresh = self.refresh_token
            if not refresh:
                raise SesarAuthError(
                    "SESAR access token is missing or expired and no refresh "
                    "token is configured. Add tokens in Settings → SESAR.")
            url = self.base_url + "auth/token/refresh/"
            log = get_sesar_logger()
            log.info(f"Refreshing SESAR access token [env={self.environment}]")
            try:
                resp = self.session.post(url, json={"refresh": refresh},
                                         timeout=self.timeout)
            except requests.RequestException as exc:
                raise SesarConnectionError(f"Could not reach SESAR to refresh token: {exc}",
                                           url=url) from exc
            if resp.status_code != 200:
                err = self._error_from_response(resp)
                log.error(f"Token refresh failed [HTTP {resp.status_code}]: {err.message}")
                raise SesarAuthError(
                    "SESAR rejected the refresh token (it may have expired, been "
                    "revoked, or already been used). Generate a new token pair in "
                    "SESAR Developer Settings and paste it into Settings → SESAR.",
                    status=resp.status_code, url=url)
            body = self._json(resp)
            data = body.get("data") if isinstance(body.get("data"), dict) else body
            access, new_refresh = data.get("access"), data.get("refresh")
            if not access:
                raise SesarAuthError("Token refresh response did not contain an access token.",
                                     status=resp.status_code, url=url)
            # Persist immediately — the old refresh token is already revoked.
            self.tokens.set_pair(self.environment, access, new_refresh or refresh)
            log.info("SESAR token refreshed and saved")
            return access

    def _valid_access_token(self) -> Optional[str]:
        """Current access token, refreshed proactively if about to expire."""
        token = self.access_token
        if token:
            exp = jwt_expiry(token)
            if exp is None or exp - time.time() > REFRESH_SKEW_SECONDS:
                return token
        if self.refresh_token:
            return self.refresh_tokens()
        return token  # may be None or expired; the server will say so

    # -- core request ------------------------------------------------------
    def _request(self, method: str, path: str, *, auth: str = "optional",
                 params: Optional[Dict[str, Any]] = None,
                 json_body: Optional[Dict[str, Any]] = None,
                 expected: Iterable[int] = (200,)) -> Any:
        """
        auth: "none" | "optional" (send token if we have one) | "required".
        On 401 with a refresh token available, refresh once and retry.
        """
        url = self.base_url + path.lstrip("/")
        log = get_sesar_logger()
        headers: Dict[str, str] = {}
        token = None
        if auth != "none":
            token = self._valid_access_token() if self.has_credentials() else None
            if auth == "required" and not token:
                raise SesarAuthError(
                    "This action needs a SESAR JSON Web Token. Add your access and "
                    "refresh tokens in Settings → SESAR.")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if json_body is not None:
            headers["Content-Type"] = "application/json"

        clean_params = {k: v for k, v in (params or {}).items() if v not in (None, "")}

        for attempt in (1, 2):
            t0 = time.perf_counter()
            try:
                resp = self.session.request(method, url, params=clean_params or None,
                                            json=json_body, headers=headers,
                                            timeout=self.timeout)
            except requests.Timeout as exc:
                raise SesarConnectionError("SESAR did not respond in time.", url=url) from exc
            except requests.ConnectionError as exc:
                raise SesarConnectionError(
                    "Could not connect to the SESAR API. Check your internet connection.",
                    url=url) from exc
            except requests.RequestException as exc:
                raise SesarConnectionError(f"SESAR request failed: {exc}", url=url) from exc

            log.debug(f"{method} {resp.url} -> {resp.status_code} "
                      f"({(time.perf_counter() - t0) * 1000:.0f} ms)")

            if resp.status_code == 401 and token and attempt == 1 and self.refresh_token:
                token = self.refresh_tokens()
                headers["Authorization"] = f"Bearer {token}"
                continue
            break

        if resp.status_code in expected:
            if resp.status_code == 204 or not resp.content:
                return {}
            return self._json(resp)
        raise self._error_from_response(resp)

    @staticmethod
    def _json(resp: requests.Response) -> Any:
        try:
            return resp.json()
        except ValueError:
            ctype = resp.headers.get("Content-Type", "?")
            snippet = (resp.text or "").strip()[:200].replace("\n", " ")
            raise SesarApiError(
                f"SESAR returned non-JSON content (Content-Type: {ctype}). "
                f"First 200 chars: {snippet or '<empty body>'}",
                status=resp.status_code, url=resp.url) from None

    @staticmethod
    def _error_from_response(resp: requests.Response) -> SesarApiError:
        status = resp.status_code
        message, errors = None, None
        try:
            body = resp.json()
        except ValueError:
            body = None
        if isinstance(body, dict):
            message = body.get("message") or body.get("detail") or body.get("error")
            errors = body.get("errors")
            if errors is None:
                # DRF-style validation: {"field": ["msg", ...], ...}
                field_errs = {k: v for k, v in body.items()
                              if k not in ("message", "detail", "error", "code", "status")}
                errors = field_errs or None
        elif isinstance(body, list):
            errors = body
        if not message:
            message = {400: "SESAR rejected the request.",
                       401: "SESAR authentication failed.",
                       403: "You don't have permission for this action on SESAR.",
                       404: "Not found on SESAR.",
                       429: "SESAR rate limit reached — wait a moment and try again."}.get(
                status, f"SESAR returned an error (HTTP {status}).")
            if body is None and resp.text:
                message += f" {resp.text.strip()[:200]}"
        cls = {400: SesarValidationError, 401: SesarAuthError,
               403: SesarPermissionError, 404: SesarNotFoundError}.get(status, SesarApiError)
        return cls(str(message), status=status, errors=errors, url=resp.url)

    # -- public API ----------------------------------------------------------
    def search(self, q: Optional[str] = None, *, name: Optional[str] = None,
               igsn: Optional[str] = None, object_type: Optional[str] = None,
               country: Optional[str] = None, scope: Optional[str] = None,
               is_draft: Optional[bool] = None, page: int = 1,
               page_size: int = 25) -> SearchPage:
        """GET samples/ — search/list. Token optional (public results without one)."""
        page_size = max(1, min(int(page_size), MAX_PAGE_SIZE))
        params = {"q": q, "name": name, "igsn": igsn, "object_type": object_type,
                  "country": country, "scope": scope, "page": page,
                  "page_size": page_size}
        if is_draft is not None:
            params["is_draft"] = "true" if is_draft else "false"
        auth = "required" if scope in ("personal", "shared", "personal_and_shared") else "optional"
        body = self._request("GET", "samples/", auth=auth, params=params)
        result = _parse_search_envelope(body, page, page_size)
        get_sesar_logger().info(
            f"SESAR search [q={q!r}, scope={scope or 'default'}, page={result.page}/"
            f"{result.total_pages}] -> {len(result.items)} of {result.count}")
        return result

    def get_sample(self, igsn: str) -> Dict[str, Any]:
        """
        GET samples/{igsn}/ — fetch one sample by IGSN.

        If the user typed a bare code (no "10.xxxxx/" prefix) and the direct
        fetch 404s, fall back to an `igsn=` search and fetch the unique exact
        match. That keeps "TAP00002Y" working without hard-coding a prefix
        (sandbox and production may use different ones).
        """
        igsn = normalize_igsn(igsn)
        if not igsn:
            raise SesarValidationError("No IGSN given.")
        try:
            return unwrap_sample(self._request("GET", f"samples/{igsn_path(igsn)}/"))
        except SesarNotFoundError:
            if has_doi_prefix(igsn):
                raise
            page = self.search(igsn=igsn, page_size=10)
            exact = [s for s in page.items
                     if bare_igsn(str(s.get("igsn", ""))).upper() == igsn.upper()]
            if len(exact) == 1 and exact[0].get("igsn"):
                return unwrap_sample(
                    self._request("GET", f"samples/{igsn_path(exact[0]['igsn'])}/"))
            raise

    def update_sample(self, igsn: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        PATCH samples/{igsn}/ — send only the fields to change.

        Guards against things the API rejects anyway, with clearer messages:
        igsn/sesar_code can't change; latitude/longitude can't be cleared.
        Note: list fields in PATCH_REPLACED_LISTS overwrite the remote list.
        """
        igsn = normalize_igsn(igsn)
        if not changes:
            raise SesarValidationError("Nothing to update — no fields were selected.")
        bad = sorted(set(changes) & PATCH_FORBIDDEN_FIELDS)
        if bad:
            raise SesarValidationError(f"These fields cannot be changed with PATCH: {', '.join(bad)}")
        nulled = [k for k in ("latitude", "longitude") if k in changes and changes[k] is None]
        if nulled:
            raise SesarValidationError(
                "Latitude/longitude cannot be cleared once set (null is rejected by SESAR).")
        get_sesar_logger().info(
            f"SESAR PATCH [igsn={igsn}, fields={sorted(changes)}]")
        return unwrap_sample(self._request("PATCH", f"samples/{igsn_path(igsn)}/",
                                           auth="required", json_body=changes))

    def register_sample(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST samples/ — register a new sample; SESAR mints the IGSN.

        Publishing requires name, object_type, latitude, longitude and
        sesar_code. Drafts (`is_draft: true`) may omit coordinates.
        Returns the created sample (contains the new `igsn`).
        """
        # Dropping empty values also drops an empty "igsn" so SESAR mints one.
        body = {k: v for k, v in payload.items() if v not in (None, "", [])}
        missing = [k for k in ("name", "object_type") if not body.get(k)]
        if not body.get("is_draft"):
            missing += [k for k in ("latitude", "longitude", "sesar_code") if body.get(k) in (None, "")]
        if missing:
            raise SesarValidationError(
                "Missing required field(s) for registration: " + ", ".join(missing)
                + ("" if body.get("is_draft") else
                   "\n\n(Save as a draft to register without coordinates.)"))
        get_sesar_logger().info(
            f"SESAR POST register [name={body.get('name')!r}, draft={bool(body.get('is_draft'))}]")
        return unwrap_sample(self._request("POST", "samples/", auth="required",
                                           json_body=body, expected=(200, 201)))

    def whoami(self) -> Dict[str, Any]:
        """GET users/me/ — verifies the token (used by Settings → Test connection)."""
        body = self._request("GET", "users/me/", auth="required")
        return body.get("data", body) if isinstance(body, dict) else {}
