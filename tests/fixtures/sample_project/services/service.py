"""Sample service module - imports from models."""

from sample_project.models.model import User


class UserService:
    def get_user(self, name: str) -> User:
        return User(name=name, email=f"{name}@example.com")
