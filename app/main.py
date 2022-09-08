from fastapi import Depends, FastAPI

from app.config import in_memory_db
from app.service_layer import services
from app.service_layer.unit_of_work import SqlAlchemyUnitOfWork

app = FastAPI()


@app.on_event("startup")
async def startup():
    await in_memory_db()


@app.post("/books")
async def ct_book(
    name: str,
    author: str,
    release_year: int,
    uow: SqlAlchemyUnitOfWork = Depends(),
):
    return await services.create_book(uow, name, author, release_year)


@app.get("/books")
async def get_books(uow: SqlAlchemyUnitOfWork = Depends()):
    books = await services.get_all_books(uow=uow)
    return books


@app.get("/books/{book_name}")
async def get_book(book_name: str, uow: SqlAlchemyUnitOfWork = Depends()):
    book = await services.get_book(uow=uow, book_name=book_name)
    return book


@app.put("/books/{book_id}")
async def update_book(
    book_id: int,
    name: str | None = None,
    author: str | None = None,
    release_year: int | None = None,
    uow: SqlAlchemyUnitOfWork = Depends(),
):
    await services.update_book(
        book_id=book_id,
        name=name,
        author=author,
        release_year=release_year,
        uow=uow,
    )


@app.post("/readers")
async def create_reader(name: str, uow: SqlAlchemyUnitOfWork = Depends()):
    return await services.create_reader(uow=uow, name=name)


@app.patch("/readers")
async def get_reader_a_book(
    reader_name, book_name, uow: SqlAlchemyUnitOfWork = Depends()
):
    return await services.buy_book(
        uow=uow, reader_name=reader_name, book_name=book_name
    )


@app.get("/readers")
async def get_reader(reader_name, uow: SqlAlchemyUnitOfWork = Depends()):
    return await services.get_reader(uow=uow, reader_name=reader_name)
