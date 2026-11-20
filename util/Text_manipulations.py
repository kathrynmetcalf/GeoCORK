import re
from difflib import SequenceMatcher
from pathlib import Path


def remove_spaces(text: str):
    new_text = text.replace(" ", "")
    return new_text


def add_spaces_camel(text: str):
    re_outer = re.compile(r'([^A-Z ])([A-Z])')
    re_inner = re.compile(r'\b[A-Z]+(?=[A-Z][a-z])')
    new_text = (re_inner.sub(r'\g<0> ', re_outer.sub(r'\1 \2', text)))
    if "/ " in new_text:
        new_text = new_text.replace("/ ", "/")
    if "( " in new_text:
        new_text = new_text.replace("( ", "(")
    return new_text


def shrink_home(path: str) -> str:
    """Convert full home path to tilde-style for display."""
    home = str(Path.home()).replace('\\', '/')
    return str(path).replace(home, "~")


def expand_home(path: str) -> str:
    """Convert tilde path back to absolute path."""
    full_path = str(Path(path).expanduser()).replace('\\', '/')
    return full_path


def merge_intervals(intervals):
    intervals = sorted(intervals)
    merged = []
    for a, b in intervals:
        if not merged or a > merged[-1][1]:
            merged.append([a, b])
        else:
            merged[-1][1] = max(merged[-1][1], b)
    return [(a, b) for a, b in merged]


def intersect_intervals(a, b):
    output = []
    i = j = 0
    while i < len(a) and j < len(b):
        a0, a1 = a[i]
        b0, b1 = b[j]
        lo, hi = max(a0, b0), min(a1, b1)
        if hi > lo:
            output.append((lo, hi))
        if a1 < b1:
            i += 1
        else:
            j += 1
    return output


def common_strings(strings: list[str] | None) -> str:
    """
    Find text common to ALL strings. Replace unique chunks with the placeholder [-]
    """
    # Minimum length of common string to match, reduce noise
    minimum_length = 2
    placeholder = "[-]"
    strings = [s for s in strings if s is not None]
    if not strings:
        return "-"

    # Begin with the first string and build matches from there
    base = strings[0]
    common_regions = [(0, len(base))]

    for s in strings[1:]:
        sequence_matches = SequenceMatcher(None, base, s)
        matches = [(m.a, m.a + m.size) for m in sequence_matches.get_matching_blocks() if m.size >= minimum_length]
        matches = merge_intervals(matches)
        common_regions = intersect_intervals(common_regions, matches)
        if not common_regions:
            break

    # Build string using common regions
    parts = []
    last = 0
    for a, b in common_regions:
        if a > last:
            parts.append(placeholder)
        parts.append(base[a:b])
        last = b
    if last < len(base):
        parts.append(placeholder)
    elif len(parts) == 1 and parts[0] in strings:
        # One string is the exact same as the base, so do not include the last character
        parts[0] = parts[0][0:-1]
        parts.append(placeholder)
    output = []
    for part in parts:
        if output and output[-1] == placeholder and part == placeholder:
            # Don't have two placeholders in a row
            continue
        output.append(part)

    return "".join(output)

def strip_strings(x):
    """
    Remove excess white space from strings. Returns the data unchanged if not a string.
    :param x: Value from a DataFrame.
    :return: Stripped value if string, unchanged if another data type.
    """
    if isinstance(x, str):
        return x.strip()
    return x
