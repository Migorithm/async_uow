from app.domain.models import Book, Reader
from app.service_layer.unit_of_work import SqlAlchemyUnitOfWork

from .exceptions import BookNotfound, ReaderNotFound


async def create_book(
    uow: SqlAlchemyUnitOfWork, name: str, author: str, release_year: int
):
    async with uow:
        new_book = Book(name=name, author=author, release_year=release_year)
        uow.books.add(new_book)
        await uow.commit()


async def get_all_books(uow: SqlAlchemyUnitOfWork) -> list[Book]:
    async with uow:
        uow.books._base_query = uow.books._base_query.order_by(Book.id)
        books = await uow.books.list()
        return books


async def get_book(uow: SqlAlchemyUnitOfWork, book_name: str):
    async with uow:
        book: Book = await uow.books.filter(Book.name == book_name).get()
        return book


async def update_book(
    uow: SqlAlchemyUnitOfWork,
    book_id: int,
    name: str | None = None,
    author: str | None = None,
    release_year: int | None = None,
):
    async with uow:
        book: Book = uow.books.get(uow.books.filter(Book.id == book_id))
        if name:
            book.name = name
        if author:
            book.author = author
        if release_year:
            book.release_year = release_year
        await uow.commit()


async def create_reader(uow: SqlAlchemyUnitOfWork, name):
    async with uow:
        new_reader = Reader(name=name)
        uow.readers.add(new_reader)
        await uow.commit()


async def buy_book(uow: SqlAlchemyUnitOfWork, reader_name, book_name):
    # note that LIMIT 1 is not automatically supplied, if needed
    async with uow:
        uow.readers.load_childs()
        reader: Reader = await uow.readers.filter(
            Reader.name == reader_name
        ).get()
        if not reader:
            raise ReaderNotFound

        book: Book = await uow.books.filter(Book.name == book_name).get()
        if not book:
            raise BookNotfound

        reader.books.append(book)
        await uow.session.commit()


async def get_reader(uow: SqlAlchemyUnitOfWork, reader_name):
    async with uow:
        uow.readers.load_childs()
        reader: Reader = await uow.readers.filter(
            Reader.name == reader_name
        ).get()
        return reader
