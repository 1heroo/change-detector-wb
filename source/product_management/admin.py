from sqladmin import ModelView
from source.product_management.models import Product, ProductHistory, Characteristic, Shop


class ShopAdmin(ModelView, model=Shop):
    column_list = ['id', 'name', 'supplier', 'is_active']
    column_searchable_list = ['name']


class ProductAdmin(ModelView, model=Product):
    column_list = ['nm_id', 'vendor_code', 'brand', 'salePriceU', 'clientSale', 'updated_at']
    column_formatters = {Product.vendor_code: lambda item, _: item.vendor_code[:20]}
    column_searchable_list = ['nm_id', 'brand']


class CharacteristicAdmin(ModelView, model=Characteristic):
    column_list = ['product_nm_id', 'name', 'value']
    column_formatters = {'name': lambda item, _: item.name[:20]}
    column_searchable_list = ['product_nm_id']


class ProductHistoryAdmin(ModelView, model=ProductHistory):
    column_list = ['nm_id', 'action', 'created_at']
    column_searchable_list = ['nm_id', 'action']
    column_formatters = {'action': lambda item, _: item.action[:60]}
    column_default_sort = [(ProductHistory.created_at, True)]
