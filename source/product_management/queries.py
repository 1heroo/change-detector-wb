from source.db.db import async_session
import sqlalchemy as sa
from source.product_management.models import Product, Characteristic, ProductHistory, Shop, Order
from source.db.queries import BaseQueries


class ShopQueries(BaseQueries):
    model = Shop

    async def fetch_all(self) -> list[Shop]:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model)
            )
            return result.scalars().all()

    async def get_shop_by_id(self, shop_id: int) -> Shop | None:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model).where(self.model.id == shop_id)
            )
            return result.scalars().first()


class ProductQueries(BaseQueries):

    model = Product

    async def fetch_all(self) -> list[Product]:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model)
            )
            return result.scalars().all()

    async def get_products_by_shop_id(self, shop_id: int):
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model).where(self.model.shop_id == shop_id)
            )
            return result.scalars().all()


class CharacteristicQueries(BaseQueries):
    model = Characteristic

    async def fetch_all(self) -> list[Characteristic]:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model)
            )
            return result.scalars().all()

    async def delete_instances(self, instances: list[Characteristic]) -> None:
        for instance in instances:
            await self.delete_instance(instance=instance)


class ProductHistoryQueries(BaseQueries):
    model = ProductHistory

    async def fetch_all(self) -> list[ProductHistory]:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model)
            )
            return result.scalars().all()


class OrderQueries(BaseQueries):
    model = Order

    async def fetch_all(self) -> list[Order]:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model)
            )
            return result.scalars().all()

    async def get_orders_by_shop_id(self, shop_id: int) -> list[Order]:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model).where(self.model.shop_id == shop_id)
            )
            return result.scalars().all()

    async def get_not_completed_and_canceled_orders_by_shop_id(self, shop_id: int) -> list[Order]:
        async with async_session() as session:
            result = await session.execute(
                sa.select(self.model)
                .where(self.model.status != 'complete')
                .where(self.model.status != 'cancel')
                .where(self.model.shop_id == shop_id)
            )
            return result.scalars().all()
        