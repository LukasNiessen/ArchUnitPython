"""Sample service B - imports from service using relative import."""

from .service import UserService


class AnotherService:
    def __init__(self):
        self.user_service = UserService()
