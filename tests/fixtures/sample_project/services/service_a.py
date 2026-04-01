"""Sample service A - imports from service."""

from sample_project.services.service import UserService


class ExtendedService(UserService):
    pass
