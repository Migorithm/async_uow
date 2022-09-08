from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, Literal, Type, TypeVar

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.selectable import Select

ModelType = TypeVar("ModelType", bound=object)
LOGICAL_OPERATOR = Literal["and", "or"]


class LogicalOperatorMustBeGiven(Exception):
    pass


class AbstractRepository(ABC):
    def add(self):
        ...

    async def get(self):
        return await self._get()

    async def list(self):
        return await self._list()

    def filter(self, condition, logical_operator: LOGICAL_OPERATOR = "and"):
        self._filter(condition, logical_operator=logical_operator)
        return self

    @abstractmethod
    def _get(self):
        raise NotImplementedError

    @abstractmethod
    def _list(self):
        raise NotImplementedError

    @abstractmethod
    def _filter(self, condition, logical_operator: LOGICAL_OPERATOR):
        raise NotImplementedError


class AsyncSqlAlchemyRepository(Generic[ModelType], AbstractRepository):
    def __init__(self, *, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self._base_query: Select = select(self.model)
        self.session = session

    def add(self, model):
        self.session.add(model)

    async def _get(self):
        q = await self.session.execute(self._base_query.limit(1))
        return q.scalars().first()

    async def _list(self):
        q = await self.session.execute(self._base_query)
        return q.scalars().all()

    def _filter(self, condition, logical_operator: LOGICAL_OPERATOR):
        match condition:
            case Sequence():
                if logical_operator == "and":
                    self._base_query = self._base_query.where(and_(*condition))
                else:
                    self._base_query = self._base_query.where(or_(*condition))
            case BinaryExpression():  # type: ignore
                self._base_query = self._base_query.where(condition)
            case _:
                raise LogicalOperatorMustBeGiven

    def load_childs(self):
        self._base_query: Select = select(self.model)
        self._loader = selectinload(None)
        # Recursive call
        self._load_childs(model=self.model)

        self._base_query = self._base_query.options(self._loader)

    def _load_childs(self, model=None):
        if (
            child_list := [
                k
                for k, v in model.__annotations__.items()
                if v.startswith("list")
            ]
        ) is None:
            return
        else:
            # parent_name = model.__name__.lower()
            for key in child_list:
                child_model = getattr(self.model, key).property.mapper.class_
                self.loader = self._loader.selectinload(
                    getattr(self.model, key)
                )
                self._load_childs(model=child_model)
