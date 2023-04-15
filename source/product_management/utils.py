import datetime

from source.core.base_utils import BaseUtils
import asyncio

from source.product_management.models import Product, Characteristic, Order


class ProductUtils(BaseUtils):

    @staticmethod
    def prepare_products_for_saving(
            products: list[dict], shop_id: int = None, shops_supplier: str = None) -> tuple:
        products_to_be_saved = []
        characteristics_to_be_saved = []
        for product in products:
            extended = product['detail'].get('extended', {})
            product_to_be_saved = Product(
                nm_id=product['card'].get('nm_id'),
                vendor_code=product['card'].get('vendor_code'),
                brand=product['detail'].get('brand'),
                subj_name=product['card'].get('subj_root_name'),
                subj_root_name=product['card'].get('subj_name'),
                imt_name=product['card'].get('imt_name'),
                name=product['detail'].get('name'),
                description=product['card'].get('description'),

                priceU=product['detail'].get('priceU', 0) // 100,
                salePriceU=product['detail'].get('salePriceU', 0) // 100,
                clientSale=extended.get('clientSale'),
                basicSale=extended.get('basicSale'),
                shop_id=shop_id,
                shops_supplier=shops_supplier
            )
            products_to_be_saved.append(product_to_be_saved)
            for option in product['card'].get('options', []):
                characteristics_to_be_saved.append(Characteristic(
                    name=option.get('name'),
                    value=option.get('value'),
                    product_nm_id=product_to_be_saved.nm_id
                ))
        return products_to_be_saved, characteristics_to_be_saved

    @staticmethod
    def prepare_orders_for_saving(orders: list[dict], shop_id: int, orderUid: str = 'orderUid') -> list[Order]:
        return [
            Order(
                orderUid=order.get(orderUid) + 'canceled' if order.get('isCancel') else order.get(orderUid),
                nm_id=order.get('nmId'),
                shop_id=shop_id
            )
            for order in orders
        ]

    @staticmethod
    def filter_recently_added_orders(orders: list[Order]) -> list[Order]:
        pass


class WbApiUtils(BaseUtils):

    @staticmethod
    def auth(api_key: str) -> dict:
        return {
            'Authorization': api_key
        }

    async def get_shops_orders(self, token_auth: dict) -> list[dict]:
        url = 'https://suppliers-api.wildberries.ru/api/v3/orders/new'
        data = await self.make_get_request(url=url, headers=token_auth)
        return data.get('orders', [])

    async def get_shops_orders_fbo(self, token_auth: dict) -> list[dict]:
        dateFrom = datetime.datetime.now() - datetime.timedelta(weeks=4)
        url = f'https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom={str(dateFrom).replace(" ", "T")}'
        data = await self.make_get_request(url=url, headers=token_auth)
        return data


class ParsingUtils(BaseUtils):

    async def get_product_data(self, article):
        card_url = self.make_head(int(article)) + self.make_tail(str(article), 'ru/card.json')
        obj = {}
        card = await self.make_get_request(url=card_url, headers={})

        detail_url = f'https://card.wb.ru/cards/detail?spp=27&regions=80,64,38,4,83,33,68,70,69,30,86,75,40,1,22,66,31,48,110,71&pricemarginCoeff=1.0&reg=1&appType=1&emp=0&locale=ru&lang=ru&curr=rub&couponsGeo=12,3,18,15,21&sppFixGeo=4&dest=-455203&nm={article}'
        detail = await self.make_get_request(detail_url, headers={})

        if detail:
            detail = detail['data']['products']
        else:
            detail = {}

        obj.update({
            'card': card if card else {},
            'detail': detail[0] if detail else {},
            # 'seller': seller_data if seller_data else {}
        })

        return obj

    async def get_detail_by_nms(self, nms):
        output_data = []
        tasks = []

        for index, nm in enumerate(nms):
            task = asyncio.create_task(self.get_product_data(article=nm))
            tasks.append(task)

            if index % 100 == 0:
                print(index, 'product data')
                output_data += await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []

        output_data += await asyncio.gather(*tasks, return_exceptions=True)
        output_data = [item for item in output_data if not isinstance(item, Exception) and item]
        return output_data
