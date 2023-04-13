from source.db.db import async_session
import sqlalchemy as sa
from source.product_management.models import Product, Characteristic, ProductHistory
from source.db.queries import BaseQueries


class ProductQueries(BaseQueries):

    model = Product

    async def fetch_all(self) -> list[Product]:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model)
            )
            return result.scalars().all()


class CharacteristicQueries(BaseQueries):
    model = Characteristic

    async def fetch_all(self) -> list[Product]:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model)
            )
            return result.scalars().all()


class ProductHistoryQueries(BaseQueries):
    model = ProductHistory

    async def fetch_all(self) -> list[ProductHistory]:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model)
            )
            return result.scalars().all()
