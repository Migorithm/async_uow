from collections import deque
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    event,
    func,
)
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import registry, relationship
from sqlalchemy.types import DateTime, TypeDecorator

from app.domain import models

metadata = MetaData()

mapper_registry = registry(metadata=metadata)


class SqliteDecimal(TypeDecorator):
    # This TypeDecorator use Sqlalchemy Integer as impl. It converts Decimals
    # from Python to Integers which is later stored in Sqlite database.
    impl = Integer

    def __init__(self, scale):
        # It takes a 'scale' parameter, which specifies the number of digits
        # to the right of the decimal point of the number in the column.
        TypeDecorator.__init__(self)
        self.scale = scale
        self.multiplier_int = 10**self.scale

    def process_bind_param(self, value, dialect):
        # e.g. value = Column(SqliteDecimal(2)) means a value such as
        # Decimal('12.34') will be converted to 1234 in Sqlite
        if value is not None:
            value = int(Decimal(value) * self.multiplier_int)
        return value

    def process_result_value(self, value, dialect):
        # e.g. Integer 1234 in Sqlite will be converted to Decimal('12.34'),
        # when query takes place.
        if value is not None:
            value = Decimal(value) / self.multiplier_int
        return value


class TimeStamp(TypeDecorator):
    impl = DateTime
    LOCAL_TIMEZONE = datetime.utcnow().astimezone().tzinfo
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if value.tzinfo is None:
            value = value.astimezone(self.LOCAL_TIMEZONE)

        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)


class GUID(TypeDecorator):
    impl = String
    cache_ok = False

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID())
        else:
            return dialect.type_descriptor(String(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            return "%s" % str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, UUID):
                return value
            return str(value)


NUMERIC = SqliteDecimal(4)


readers = Table(
    "readers",
    mapper_registry.metadata,
    Column("id", NUMERIC, primary_key=True),
    Column(
        "create_dt",
        sqlite.TIMESTAMP,
        default=func.now(),
        server_default=func.now(),
    ),
    Column(
        "update_dt",
        sqlite.TIMESTAMP,
        default=func.now(),
        onupdate=func.current_timestamp(),
        server_default=func.now(),
    ),
    Column("name", String, nullable=False),
)


books = Table(
    "books",
    mapper_registry.metadata,
    Column("id", NUMERIC, primary_key=True),
    Column(
        "create_dt",
        sqlite.TIMESTAMP,
        default=func.now(),
        server_default=func.now(),
    ),
    Column(
        "update_dt",
        sqlite.TIMESTAMP,
        default=func.now(),
        onupdate=func.current_timestamp(),
        server_default=func.now(),
    ),
    Column("reader_id", ForeignKey(readers.name + ".id", ondelete="cascade")),
    Column("name", String, nullable=False),
    Column("author", String, nullable=False),
    Column("release_year", NUMERIC, nullable=False),
)

items = Table(
    "items",
    mapper_registry.metadata,
    Column("id", NUMERIC, primary_key=True),
    Column(
        "create_dt",
        sqlite.TIMESTAMP,
        default=func.now(),
        server_default=func.now(),
    ),
    Column(
        "update_dt",
        sqlite.TIMESTAMP,
        default=func.now(),
        onupdate=func.current_timestamp(),
        server_default=func.now(),
    ),
    Column("reader_id", ForeignKey(readers.name + ".id", ondelete="cascade")),
    Column("name", String, nullable=False),
)


def start_mappers():
    mapper_registry.map_imperatively(
        models.Book,
        books,
        properties={
            "reader": relationship(models.Reader, back_populates="books")
        },
    )
    mapper_registry.map_imperatively(
        models.Item,
        items,
        properties={
            "reader": relationship(models.Reader, back_populates="items")
        },
    )

    mapper_registry.map_imperatively(
        models.Reader,
        readers,
        properties={
            "books": relationship(
                models.Book,
                back_populates="reader",
                cascade="all, delete-orphan",
            ),
            "items": relationship(
                models.Item,
                back_populates="reader",
                cascade="all, delete-orphan",
            ),
        },
    )


@event.listens_for(models.Book, "load")
def receive_load_trx(book, _):
    book.events = deque()
