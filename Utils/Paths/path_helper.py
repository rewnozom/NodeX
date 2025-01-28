# ./shared/utils/path_helper.py

import os
import sys
from typing import Optional
from pathlib import Path

def resolve_relative_path(base_path: str, relative_path: str, create_dirs: bool = False) -> str:
    """
    Resolves a relative path starting with ./ relative to the base path.
    
    Args:
        base_path (str): The base directory path
        relative_path (str): The relative path starting with ./
        create_dirs (bool, optional): If True, creates directories if they don't exist. Defaults to False.
        
    Returns:
        str: The absolute path
        
    Raises:
        ValueError: If base_path is empty or None
        ValueError: If relative_path is empty or None
        OSError: If path creation fails when create_dirs is True
        OSError: If base_path doesn't exist
    """
    # Input validation
    if not base_path:
        raise ValueError("Base path cannot be empty or None")
    if not relative_path:
        raise ValueError("Relative path cannot be empty or None")

    # Normalize paths
    base_path = os.path.normpath(os.path.abspath(base_path))
    
    # Verify base path exists
    if not os.path.exists(base_path):
        raise OSError(f"Base path does not exist: {base_path}")
    
    # Handle both ./ and non-./ paths
    if relative_path.startswith('./'):
        relative_path = relative_path[2:]  # Remove './' prefix
    
    # Normalize path separators for current OS
    relative_path = relative_path.replace('/', os.path.sep)
    
    # Create absolute path
    absolute_path = os.path.normpath(os.path.join(base_path, relative_path))
    
    # Ensure the resolved path is within the base path (security check)
    if not os.path.commonpath([base_path]) == os.path.commonpath([base_path, absolute_path]):
        raise ValueError(f"Resolved path {absolute_path} is outside base path {base_path}")
    
    # Create directories if requested
    if create_dirs:
        try:
            dir_path = os.path.dirname(absolute_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)
        except OSError as e:
            raise OSError(f"Failed to create directories for path {absolute_path}: {e}")
    
    return absolute_path

def get_app_root() -> str:
    """
    Get the application root directory.
    
    Returns:
        str: The absolute path to the application root directory
    """
    if getattr(sys, 'frozen', False):
        # Running in a bundle (e.g., PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Running in normal Python environment
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def is_valid_path(path: str) -> bool:
    """
    Check if a path is valid for the current operating system.
    
    Args:
        path (str): The path to validate
        
    Returns:
        bool: True if path is valid, False otherwise
    """
    try:
        if not path:
            return False
        Path(path)
        return True
    except (TypeError, ValueError):
        return False

def normalize_path(path: str) -> str:
    """
    Normalize a path string for the current operating system.
    
    Args:
        path (str): The path to normalize
        
    Returns:
        str: Normalized path
    """
    if not path:
        return path
    return os.path.normpath(path.replace('/', os.path.sep))

def ensure_dir_exists(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path (str): The directory path
        
    Returns:
        bool: True if directory exists or was created, False on failure
    """
    try:
        if not path:
            return False
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False

def get_relative_path(path: str, base_path: str) -> Optional[str]:
    """
    Get a relative path from a base path.
    
    Args:
        path (str): The path to make relative
        base_path (str): The base path to make it relative to
        
    Returns:
        Optional[str]: Relative path if successful, None if paths are on different drives
    """
    try:
        return os.path.relpath(path, base_path)
    except ValueError:
        return None