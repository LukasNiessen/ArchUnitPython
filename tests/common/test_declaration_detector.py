"""Tests for declaration detection utilities."""

from archunitpython.common.util.declaration_detector import (
    DeclarationCounts,
    count_declarations,
    is_abstract_class,
    is_abstract_method,
    is_protocol_class,
)
import ast


class TestIsAbstractClass:
    def test_abc_base(self):
        code = "class Foo(ABC): pass"
        tree = ast.parse(code)
        cls = tree.body[0]
        assert is_abstract_class(cls) is True

    def test_not_abstract(self):
        code = "class Foo: pass"
        tree = ast.parse(code)
        cls = tree.body[0]
        assert is_abstract_class(cls) is False

    def test_abstractmethod_decorator(self):
        code = """
class Foo:
    @abstractmethod
    def bar(self): pass
"""
        tree = ast.parse(code)
        cls = tree.body[0]
        assert is_abstract_class(cls) is True


class TestIsProtocolClass:
    def test_protocol_base(self):
        code = "class Foo(Protocol): pass"
        tree = ast.parse(code)
        cls = tree.body[0]
        assert is_protocol_class(cls) is True

    def test_not_protocol(self):
        code = "class Foo: pass"
        tree = ast.parse(code)
        cls = tree.body[0]
        assert is_protocol_class(cls) is False


class TestIsAbstractMethod:
    def test_abstract_method(self):
        code = """
class Foo:
    @abstractmethod
    def bar(self): pass
"""
        tree = ast.parse(code)
        method = tree.body[0].body[0]
        assert is_abstract_method(method) is True

    def test_regular_method(self):
        code = """
class Foo:
    def bar(self): pass
"""
        tree = ast.parse(code)
        method = tree.body[0].body[0]
        assert is_abstract_method(method) is False


class TestCountDeclarations:
    def test_mixed_declarations(self):
        code = """
from abc import ABC, abstractmethod
from typing import Protocol

class MyProtocol(Protocol):
    def do_something(self) -> None: ...

class BaseService(ABC):
    @abstractmethod
    def process(self): ...

class UserService(BaseService):
    def process(self):
        pass

def helper():
    pass

MY_CONSTANT = 42
"""
        counts = count_declarations(code)
        assert counts.protocols == 1
        assert counts.abstract_classes == 1
        assert counts.concrete_classes == 1
        assert counts.abstract_methods == 1
        assert counts.functions == 1
        assert counts.variables == 1

    def test_empty_source(self):
        counts = count_declarations("")
        assert counts.total == 0

    def test_syntax_error(self):
        counts = count_declarations("def :")
        assert counts.total == 0
