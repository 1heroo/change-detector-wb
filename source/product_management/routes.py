import json

import pandas as pd
from fastapi import APIRouter, File

from source.core.advertisement_api import AdvertisementApiUtils
from source.product_management.services import ProductImportServices, ProductServices

router = APIRouter(prefix='/product-management', tags=['Product Management'])

product_services = ProductServices()
product_import_services = ProductImportServices()


@router.get('/launch-product-monitoring/')
async def launch_product_monitoring():
    await product_services.product_monitoring()


@router.get('/launch-order-monitoring/')
async def launch_order_monitoring():
    await product_services.order_monitoring()


@router.post('/import-products-by-excel/')
async def import_products_by_excel(shop_id: int, file: bytes = File()):
    df = pd.read_excel(file)
    nm_id_column = df['Артикул WB'].name
    await product_import_services.import_products_by_excel(df=df, nm_id_column=nm_id_column, shop_id=shop_id)


@router.post('/test')
async def test():
    return {'address': None, 'deliveryType': 'fbs', 'user': None, 'orderUid': '101320299_aaddc0eca8a54be4b99c618db72e2b9a', 'article': '852фиолетовый', 'rid': '97c9926ca4d24bdd80b7ba2c6cc898a2', 'createdAt': '2023-04-14T15:34:45Z', 'offices': ['Москва'], 'skus': ['2034895405624'], 'prioritySc': [], 'id': 772144730, 'warehouseId': 16521, 'nmId': 87731558, 'chrtId': 142427721, 'price': 65700, 'convertedPrice': 65700, 'currencyCode': 643, 'convertedCurrencyCode': 643, 'isLargeCargo': False}