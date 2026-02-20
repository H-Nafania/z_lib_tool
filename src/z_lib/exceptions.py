class ZipNotLoadedError(Exception):
    """Raised when attempting to access a ZIP file that has not been loaded."""
    pass

class ZipAlreadyLoadedError(Exception):
    """Raised when attempting to load a ZIP file that is already loaded."""
    pass

class ZipPathError(Exception):
    """Raised when a path is invalid or cannot be resolved to a ZIP file."""
    pass
