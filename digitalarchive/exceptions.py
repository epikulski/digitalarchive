
class InvalidSearchField(Exception):
    """User attempted to search on a field not valid for a given model."""
    pass

class NoSuchResource(Exception):
    """User attempted to retrieve a resource by ID#, but no such Resource exists"""
    pass

class APIServerError(Exception):
    """DA API returned a non-200 code for attempted operation."""
    pass