"""Sample service with classes for metrics testing."""

from abc import ABC, abstractmethod
from typing import Protocol


class Serializable(Protocol):
    """Protocol for serializable objects."""

    def serialize(self) -> dict: ...


class BaseService(ABC):
    """Abstract base service."""

    def __init__(self):
        self.cache = {}
        self.db = None
        self.logger = None

    @abstractmethod
    def process(self):
        ...

    def get_cache(self):
        return self.cache

    def clear_cache(self):
        self.cache = {}


class UserService(BaseService):
    """Concrete service with multiple methods accessing different fields."""

    def __init__(self):
        super().__init__()
        self.users = []
        self.active_count = 0

    def process(self):
        self.cache["users"] = self.users
        self.active_count = len(self.users)

    def get_user(self, user_id):
        return self.db.find(user_id)

    def add_user(self, user):
        self.users.append(user)
        self.active_count += 1

    def log_action(self, action):
        self.logger.info(action)


class DataClass:
    """Simple data class with fields but minimal methods."""

    def __init__(self, name, value, category):
        self.name = name
        self.value = value
        self.category = category

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
            "category": self.category,
        }
