from __future__ import annotations

import copy
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm.exc import DetachedInstanceError


class Base:
    id: UUID
    create_dt: datetime
    update_dt: datetime
    __repr_attrs__: Sequence[str] = ["id"]

    def __name__(self):
        return super().__name__()

    def __eq__(self, other):
        if not isinstance(other, Base):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        repr_field_str = []
        for key in self.__repr_attrs__:
            try:
                repr_field_str.append(f"{key}={getattr(self,key)}")
            except DetachedInstanceError:
                repr_field_str = ["Detached Instance"]
                break

        return f"""<{self.__class__.__name__}
            ({', '.join(repr_field_str)} {hex(id(self))})>"""

    def _to_dict(self):
        if hasattr(self, "__slots__"):
            return {v: getattr(self, v) for v in self.__slots__}
        return self.__dict__


class Reader(Base):
    books: list[Book]
    items: list[Item]

    def __init__(
        self,
        name: str,
        books: list[Book] = None,
        items: list[Item] = None,
    ):
        self.name = name
        self.books = [] if books is None else copy.copy(books)
        self.items = [] if items is None else copy.copy(items)


class Book(Base):
    reader: Reader | None

    def __init__(
        self,
        name: str,
        author: str,
        release_year: int,
        reader: Reader | None = None,
        **kwargs,
    ) -> None:
        self.name = name
        self.author = author
        self.release_year = release_year
        self.reader = reader


class Item(Base):
    reader: Reader | None

    def __init__(
        self, name: str, reader: Reader | None = None, **kwargs
    ) -> None:
        self.name = name
        self.reader = reader
