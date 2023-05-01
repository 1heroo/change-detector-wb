import datetime

import pandas as pd

from source.core.advertisement_api import AdvertisementApiUtils
from source.product_management.models import Product, Characteristic, ProductHistory, Order
from source.product_management.queries import ProductQueries, CharacteristicQueries, ProductHistoryQueries, ShopQueries, \
    OrderQueries
from source.product_management.utils import ProductUtils, ParsingUtils, WbApiUtils


class ProductServices:

    def __init__(self):
        self.product_utils = ProductUtils()
        self.parsing_utils = ParsingUtils()
        self.wb_api_utils = WbApiUtils()

        self.shop_queries = ShopQueries()
        self.product_queries = ProductQueries()
        self.characteristic_queries = CharacteristicQueries()
        self.history_queries = ProductHistoryQueries()
        self.order_queries = OrderQueries()

        self.advertisement_api_utils = AdvertisementApiUtils()

    async def product_monitoring(self):
        saved_products = await self.product_queries.fetch_all()
        saved_characteristics = await self.characteristic_queries.fetch_all()

        if not saved_products or not saved_products:
            return

        parsed_products = await self.parsing_utils.get_detail_by_nms(
            nms=[product.nm_id for product in saved_products])
        parsed_products, parsed_characteristics = self.product_utils.prepare_products_for_saving(
            products=parsed_products)

        products, characteristics, chars_to_be_deleted, product_histories = await self.detect_changes(
            saved_products=saved_products, saved_characteristics=saved_characteristics,
            parsed_products=parsed_products, parsed_characteristics=parsed_characteristics
        )
        if products:
            await self.product_queries.save_in_db(products, many=True)
        if characteristics:
            await self.characteristic_queries.save_in_db(characteristics, many=True)
        if chars_to_be_deleted:
            await self.characteristic_queries.delete_instances(instances=chars_to_be_deleted)
        if product_histories:
            # await self.advertisement_api_utils.send_detected_changes(detected_changes=product_histories)
            await self.history_queries.save_in_db(product_histories, many=True)

    async def detect_changes(
            self, saved_products: list[Product], saved_characteristics: list[Characteristic],
            parsed_products: list[Product], parsed_characteristics: list[Characteristic]) -> list[dict]:

        saved_products_df = pd.DataFrame([
            {'nm_id': product.nm_id, 'saved_product': product}
            for product in saved_products
        ])
        parsed_products_df = pd.DataFrame([
            {'nm_id': product.nm_id, 'parsed_product': product}
            for product in parsed_products
        ])
        df = pd.merge(saved_products_df, parsed_products_df, how='inner', left_on='nm_id', right_on='nm_id')

        saved_characteristics_dict = dict()
        parsed_characteristics_dict = dict()
        for characteristic in saved_characteristics:
            if saved_characteristics_dict.get(characteristic.product_nm_id):
                saved_characteristics_dict[characteristic.product_nm_id].append(characteristic)
            else:
                saved_characteristics_dict[characteristic.product_nm_id] = [characteristic]

        for characteristic in parsed_characteristics:
            if parsed_characteristics_dict.get(characteristic.product_nm_id):
                parsed_characteristics_dict[characteristic.product_nm_id].append(characteristic)
            else:
                parsed_characteristics_dict[characteristic.product_nm_id] = [characteristic]

        products_to_be_saved = []
        characteristics_to_be_saved = []
        characteristics_to_be_deleted = []
        product_history_to_be_saved = []
        for index in df.index:
            saved_product: Product = df['saved_product'][index]
            parsed_product: Product = df['parsed_product'][index]
            saved_product_characteristics = saved_characteristics_dict.get(saved_product.nm_id, [])
            parsed_product_characteristics = parsed_characteristics_dict.get(parsed_product.nm_id, [])

            product_to_be_saved, product_history_list = await self.detect_change_in_product(
                saved_product=saved_product, parsed_product=parsed_product)

            chars_to_be_saved, chars_to_be_deleted, char_history = await self.detect_change_in_characteristics(
                saved_characteristics=saved_product_characteristics,
                parsed_characteristics=parsed_product_characteristics,
                product_nm_id=saved_product.nm_id,
                shop_id=saved_product.shop_id,
                shops_supplier=saved_product.shops_supplier,
            )
            if product_to_be_saved:
                products_to_be_saved.append(product_to_be_saved)

            characteristics_to_be_saved += chars_to_be_saved
            characteristics_to_be_deleted += chars_to_be_deleted
            product_history_to_be_saved += product_history_list + char_history

        return products_to_be_saved, characteristics_to_be_saved, characteristics_to_be_deleted, product_history_to_be_saved

    @staticmethod
    async def detect_change_in_product(saved_product: Product, parsed_product: Product) -> list[ProductHistory]:
        actions = []
        if saved_product.vendor_code != parsed_product.vendor_code:
            actions.append(f'Замечено изменение вендор кода товара \n с {saved_product.vendor_code} на {parsed_product.vendor_code}')
            saved_product.vendor_code = parsed_product.vendor_code

        if saved_product.brand != parsed_product.brand:
            actions.append(
                f'Замечено изменение бренда товара \n с "{saved_product.brand}" на "{parsed_product.brand}"')
            saved_product.brand = parsed_product.brand

        if saved_product.subj_name != parsed_product.subj_name:
            actions.append(f'Замечено изменение подкатегории товара \n с "{saved_product.subj_name}" на "{parsed_product.subj_name}"')
            saved_product.subj_name = parsed_product.subj_name

        if saved_product.imt_name != parsed_product.imt_name:
            actions.append(f'Замечено изменение imt_name товара \n с "{saved_product.imt_name}" на "{parsed_product.imt_name}"')
            saved_product.imt_name = parsed_product.imt_name

        if saved_product.name != parsed_product.name:
            actions.append(f'Замечено изменение в наименовании товара \n с "{saved_product.name}" на "{parsed_product.name}"')
            saved_product.name = parsed_product.name

        if saved_product.description != parsed_product.description:
            actions.append(f'Замечено изменение в описании товара \n с "{saved_product.description}" на "{parsed_product.description}"')
            saved_product.description = parsed_product.description

        if saved_product.priceU != parsed_product.priceU:
            actions.append(f'Замечено изменение в цене товара до скидки\n с "{saved_product.priceU}" на "{parsed_product.priceU}"')
            saved_product.priceU = parsed_product.priceU

        if saved_product.salePriceU != parsed_product.salePriceU:
            actions.append(f'Замечено изменение в цене товара после скидки\n с "{saved_product.salePriceU}" на "{parsed_product.salePriceU}"')
            saved_product.salePriceU = parsed_product.salePriceU

        if saved_product.clientSale != parsed_product.clientSale:
            actions.append(f'Замечено изменение скидки товара ССП\n с "{saved_product.clientSale}" на "{parsed_product.clientSale}"')
            saved_product.clientSale = parsed_product.clientSale

        if saved_product.basicSale != parsed_product.basicSale:
            actions.append(f'Замечено изменение скидки покупателя товара \n с "{saved_product.basicSale}" на "{parsed_product.basicSale}"')
            saved_product.basicSale = parsed_product.basicSale

        if actions:
            saved_product.updated_at = datetime.datetime.now()
            return saved_product, [
                ProductHistory(
                    nm_id=saved_product.nm_id,
                    action=action,
                    created_at=datetime.datetime.now(),
                    shop_id=saved_product.shop_id,
                    shops_supplier=saved_product.shops_supplier,
                )
                for action in actions
            ]
        return None, []

    @staticmethod
    async def detect_change_in_characteristics(
            saved_characteristics: list[Characteristic],
            parsed_characteristics: list[Characteristic],
            product_nm_id: int,
            shop_id: int,
            shops_supplier: str,
    ) -> list[ProductHistory]:
        saved_characteristics_df = pd.DataFrame([
            {
                'nm_id': characteristic.product_nm_id,
                'keyword': characteristic.name,
                'saved_characteristic': characteristic}
            for characteristic in saved_characteristics
        ])
        parsed_characteristics_df = pd.DataFrame([
            {
                'nm_id': characteristic.product_nm_id,
                'keyword': characteristic.name,
                'parsed_characteristic': characteristic
            }
            for characteristic in parsed_characteristics
        ])
        df = pd.merge(saved_characteristics_df, parsed_characteristics_df, how='outer',
                      left_on=['nm_id', 'keyword'], right_on=['nm_id', 'keyword'])

        characteristics_to_be_saved = []
        characteristics_to_be_deleted = []
        actions = []

        for index in df.index:
            saved_characteristic = df['saved_characteristic'][index]
            parsed_characteristic = df['parsed_characteristic'][index]

            if pd.isna(saved_characteristic):
                actions.append(f'Добавлена новая характеристика товара с названием {parsed_characteristic.name} и со значением {parsed_characteristic.value}')
                characteristics_to_be_saved.append(parsed_characteristic)
                continue

            if pd.isna(parsed_characteristic):
                actions.append(f'Удалена характеристика товара с названием {saved_characteristic.name} и со значением {saved_characteristic.value}')
                characteristics_to_be_deleted.append(saved_characteristic)
                continue

            if saved_characteristic.value != parsed_characteristic.value:
                actions.append(f'Поменялось значение характеристики {saved_characteristic.name} с {saved_characteristic.value} на {parsed_characteristic.value}')
                saved_characteristic.value = parsed_characteristic.value
                characteristics_to_be_saved.append(saved_characteristic)

        if actions:
            return characteristics_to_be_saved, characteristics_to_be_deleted, [
                ProductHistory(
                    nm_id=product_nm_id,
                    action=action,
                    created_at=datetime.datetime.now(),
                    shop_id=shop_id,
                    shops_supplier=shops_supplier
                )
                for action in actions
            ]
        return characteristics_to_be_saved, characteristics_to_be_deleted, []

    async def order_monitoring(self):
        shops = await self.shop_queries.fetch_all()

        for shop in shops:
            statistic_auth = self.wb_api_utils.auth(api_key=shop.api_token_statistic)
            standard_auth = self.wb_api_utils.auth(api_key=shop.api_token_standard)

            orders = await self.wb_api_utils.get_shops_orders(token_auth=standard_auth)
            orders = self.product_utils.prepare_orders_for_saving(orders=orders, shop_id=shop.id, object='id')

            fbo_orders = await self.wb_api_utils.get_shops_orders_fbo(token_auth=statistic_auth)
            fbo_orders = self.product_utils.prepare_orders_for_saving(
                orders=fbo_orders, shop_id=shop.id, object='srid')

            sales = await self.wb_api_utils.get_shops_sales(token_auth=statistic_auth)
            sales = self.product_utils.prepare_orders_for_saving(orders=sales, shop_id=shop.id, object='saleID')

            orders += fbo_orders + sales

            saved_orders = await self.order_queries.get_orders_by_shop_id(shop_id=shop.id)
            saved_orders_dict = dict()
            for saved_order in saved_orders:
                saved_orders_dict[saved_order.orderUid] = True

            saved_products = await self.product_queries.get_products_by_shop_id(shop_id=shop.id)
            saved_products_dict = dict()

            for saved_product in saved_products:
                saved_products_dict[saved_product.nm_id] = True

            orders = [order for order in orders
                      if not saved_orders_dict.get(order.orderUid) and not saved_products_dict.get(order.nm_id)]

            history = []
            for order in orders:
                if order.status == 'new':
                    action = f'Новое сборочное задание у товара с артикулом {order.nm_id}'
                elif order.orderUid[0] in ['S', 'R']:
                    action = f'Продажа товара с артикулом {order.nm_id}' if order.orderUid[0] == 'S' else \
                        f"Возврат товара с артикулом {order.nm_id}"
                else:
                    action = f'Новый заказ у товара с артикулом {order.nm_id}' if 'canceled' not in order.orderUid else \
                        f'Отмена заказа у товара с артикулом {order.nm_id}'

                history.append(ProductHistory(
                    nm_id=order.nm_id,
                    action=action,
                    created_at=datetime.datetime.now(),
                    shop_id=shop.id,
                    shops_supplier=shop.supplier
                ))
            if history:
                await self.advertisement_api_utils.send_detected_changes(detected_changes=history)

                await self.history_queries.save_in_db(instances=history, many=True)
                await self.order_queries.save_in_db(instances=orders, many=True)

    async def order_status_monitoring(self):
        for shop in await self.shop_queries.fetch_all():
            standard_auth = self.wb_api_utils.auth(api_key=shop.api_token_standard)
            orders = await self.order_queries.get_not_completed_and_canceled_orders_by_shop_id(shop_id=shop.id)

            order_ids = []
            valid_orders = []
            for order in valid_orders:
                try:
                    order_id = int(order.orderUid)
                    order_ids.append(order_id)
                    orders.append(order)
                except ValueError:
                    continue
            statuses = await self.wb_api_utils.get_order_statuses(order_ids=order_ids, token_auth=standard_auth)

            orders_df = pd.DataFrame([
                {'order_id': int(order.orderUid), 'saved_order': order}
                for order in valid_orders
            ])
            statuses_df = pd.DataFrame([
                {'order_id': status.get('id', 0), 'status': status}
                for status in statuses
            ])
            if statuses_df.empty or orders_df.empty:
                continue

            df = pd.merge(orders_df, statuses_df, how='inner', left_on='order_id', right_on='order_id')

            history = []
            orders_to_be_saved = []
            for index in df.index:
                saved_order: Order = df['saved_order'][index]
                status: str = df['status'][index].get('supplierStatus', '')

                if saved_order.status != status:
                    history.append(ProductHistory(
                        nm_id=saved_order.nm_id,
                        price_for_sale=saved_order.price_for_sale,
                        action=f'Изменился статус сборочного задания с "{saved_order.status}" на "{status}"',
                        created_at=datetime.datetime.now(),
                        shops_supplier=shop.supplier,
                        shop_id=shop.id,
                    ))
                    saved_order.status = status
                    orders_to_be_saved.append(saved_order)

            if history:
                await self.advertisement_api_utils.send_detected_changes(history)
                await self.history_queries.save_in_db(instances=history, many=True)
                await self.order_queries.save_in_db(instances=orders_to_be_saved, many=True)


class ProductImportServices(ProductServices):

    async def import_products_by_excel(self, df: pd.DataFrame, nm_id_column: str, shop_id: int) -> None:
        shop = await self.shop_queries.get_shop_by_id(shop_id=shop_id)
        if not shop:
            return
        nm_ids = list(df[nm_id_column])
        products = await self.parsing_utils.get_detail_by_nms(nms=nm_ids)
        products, characteristics = self.product_utils.prepare_products_for_saving(
            products=products, shop_id=shop_id, shops_supplier=shop.supplier)
        await self.product_queries.save_in_db(instances=products, many=True)
        await self.product_queries.save_in_db(instances=characteristics, many=True)

