from __future__ import annotations

import abc

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.repository import AsyncSqlAlchemyRepository
from app.config import async_session
from app.domain.models import Book, Reader

DEFAULT_ALCHEMY_SESSION_FACTORY = async_session


class AbstractUnitOfWork(abc.ABC):
    async def __aenter__(self) -> AbstractUnitOfWork:
        return self

    @abc.abstractmethod
    async def commit(self):
        pass

    @abc.abstractmethod
    async def rollback(self):
        pass

    def collect_new_events(self):
        pass


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.session_factory = DEFAULT_ALCHEMY_SESSION_FACTORY

    async def __aenter__(self):
        self.session: AsyncSession = self.session_factory()
        async with self.session.begin():
            self.readers = AsyncSqlAlchemyRepository(
                model=Reader, session=self.session
            )
            self.books = AsyncSqlAlchemyRepository(
                model=Book, session=self.session
            )
            return await super().__aenter__()

    async def __aexit__(self, *args):
        await self.session.close()

    async def commit(self):
        await self._commit()

    async def _commit(self):
        await self.session.commit()

    async def rollback(self):
        await self._rollback()

    async def _rollback(self):
        await self.session.rollback()

    async def refresh(self, object):
        await self._refresh(object)

    async def _refresh(self, object):
        await self.session.refresh(object)

    async def flush(self):
        await self.session.flush()
