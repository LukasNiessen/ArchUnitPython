"""Error types for ArchUnitPython."""


class TechnicalError(Exception):
    """Error caused by technical issues (file system, configuration, etc.)."""

    pass


class UserError(Exception):
    """Error caused by incorrect API usage."""

    pass
