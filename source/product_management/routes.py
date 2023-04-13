import pandas as pd
from fastapi import APIRouter, File

from source.product_management.services import ProductImportServices, ProductServices

router = APIRouter(prefix='/product-management', tags=['Product Management'])

product_services = ProductServices()
product_import_services = ProductImportServices()


@router.get('/launch-product-monitoring/')
async def launch_product_monitoring():
    await product_services.product_monitoring()


@router.post('/import-products-by-excel/')
async def import_products_by_excel(file: bytes = File()):
    df = pd.read_excel(file)
    nm_id_column = df['Артикул WB'].name
    await product_import_services.import_products_by_excel(df=df, nm_id_column=nm_id_column)