class DuplicateAckNumberError(Exception):
    """Raised when an email contains an acknowledge number that already exists in the DB."""
    pass

