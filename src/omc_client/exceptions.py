class OMCError(Exception):
    """Base exception for OMC related errors."""


class OMCNotFoundError(OMCError):
    """Raised when the omc executable cannot be found."""


class OMCCommandError(OMCError):
    """Raised when an omc command fails."""


class MustGatherError(OMCError):
    """Raised when the must-gather cannot be loaded."""