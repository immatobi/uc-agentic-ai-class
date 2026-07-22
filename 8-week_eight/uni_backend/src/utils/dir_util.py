from collections.abc import Iterable
from pathlib import Path

def find_directory(dirname: str, directories: Iterable[Path]) -> Path | None:
    """
    Return the first directory whose name contains the given substring.

    Args:
        dirname: Substring to search for in directory names.
        directories: Directories to search through.

    Returns:
        The matching directory path, or None if no match is found.
        :rtype: Path | None
    """

    for dir in directories:
        if dirname in dir.name:
            return dir
        
    return None