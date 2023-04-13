import datetime

import pandas as pd

from source.product_management.models import Product, Characteristic, ProductHistory
from source.product_management.queries import ProductQueries, CharacteristicQueries, ProductHistoryQueries
from source.product_management.utils import ProductUtils, ParsingUtils


class ProductServices:

    def __init__(self):
        self.product_utils = ProductUtils()
        self.parsing_utils = ParsingUtils()

        self.product_queries = ProductQueries()
        self.characteristic_queries = CharacteristicQueries()
        self.history_queries = ProductHistoryQueries()

    async def product_monitoring(self):
        saved_products = await self.product_queries.fetch_all()
        saved_characteristics = await self.characteristic_queries.fetch_all()

        if not saved_products or not saved_products:
            return

        parsed_products = await self.parsing_utils.get_detail_by_nms(
            nms=[product.nm_id for product in saved_products])
        parsed_products, parsed_characteristics = self.product_utils.prepare_products_for_saving(
            products=parsed_products)

        products, characteristics, product_histories = await self.detect_changes(
            saved_products=saved_products, saved_characteristics=saved_characteristics,
            parsed_products=parsed_products, parsed_characteristics=parsed_characteristics
        )
        if products:
            await self.product_queries.save_in_db(products, many=True)
        if characteristics:
            await self.characteristic_queries.save_in_db(characteristics, many=True)
        if product_histories:
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
        product_history_to_be_saved = []
        for index in df.index:
            saved_product: Product = df['saved_product'][index]
            parsed_product: Product = df['parsed_product'][index]
            saved_product_characteristics = saved_characteristics_dict.get(saved_product.nm_id, [])
            parsed_product_characteristics = parsed_characteristics_dict.get(parsed_product.nm_id, [])

            product_to_be_saved, product_history_list = await self.detect_change_in_product(
                saved_product=saved_product, parsed_product=parsed_product)

            chars_to_be_saved, char_history = await self.detect_change_in_characteristics(
                saved_characteristics=saved_product_characteristics,
                parsed_characteristics=parsed_product_characteristics, product_nm_id=saved_product.nm_id
            )
            if product_to_be_saved:
                products_to_be_saved.append(product_to_be_saved)
            characteristics_to_be_saved += chars_to_be_saved
            product_history_to_be_saved += product_history_list + char_history

        return products_to_be_saved, characteristics_to_be_saved, product_history_to_be_saved

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
                    created_at=datetime.datetime.now()
                )
                for action in actions
            ]
        return None, []

    @staticmethod
    async def detect_change_in_characteristics(saved_characteristics: list[Characteristic],
                                               parsed_characteristics: list[Characteristic], product_nm_id: int) -> list[ProductHistory]:
        # parsed_characteristics += [Characteristic(name='asd', value='asd', product_nm_id=39375118)]
        # saved_characteristics += [Characteristic(name='lol', value='lol', product_nm_id=39375118)]
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
        df = pd.merge(saved_characteristics_df, parsed_characteristics_df, how='right',
                      left_on=['nm_id', 'keyword'], right_on=['nm_id', 'keyword'])

        characteristics_to_be_saved = []
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
                """НУЖНО ДОБАВИТЬ ФУНКЦИЮ УДАЛЕНИЯ УДАЛЕННОГО С ВБ ХАРАКТЕРИСТИКИ"""
                continue

            if saved_characteristic.name != parsed_characteristic.name:
                actions.append(f'Поменялось значение характеристики {saved_characteristic.name} с {saved_characteristic.value} на {parsed_characteristic.value}')
                saved_characteristic.value = parsed_characteristic.value
                characteristics_to_be_saved.append(saved_characteristic)

        if actions:
            return characteristics_to_be_saved, [
                ProductHistory(
                    nm_id=product_nm_id,
                    action=action,
                    created_at=datetime.datetime.now()
                )
                for action in actions
            ]
        return characteristics_to_be_saved, []


class ProductImportServices(ProductServices):

    async def import_products_by_excel(self, df: pd.DataFrame, nm_id_column: str) -> None:
        nm_ids = list(df[nm_id_column])
        products = await self.parsing_utils.get_detail_by_nms(nms=nm_ids)
        products, characteristics = self.product_utils.prepare_products_for_saving(products=products)
        await self.product_queries.save_in_db(instances=products, many=True)
        await self.product_queries.save_in_db(instances=characteristics, many=True)

