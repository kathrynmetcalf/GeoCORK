import re
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
    home= str(Path.home()).replace('\\', '/')
    return str(path).replace(home, "~")

def expand_home(path: str) -> str:
    """Convert tilde path back to absolute path."""
    full_path = str(Path(path).expanduser()).replace('\\', '/')
    return full_path