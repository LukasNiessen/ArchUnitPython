"""Sample controller - imports from services."""

from sample_project.services.service import UserService


class UserController:
    def __init__(self):
        self.service = UserService()

    def handle_request(self, name: str):
        return self.service.get_user(name)
