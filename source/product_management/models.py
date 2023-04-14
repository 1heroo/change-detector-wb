import sqlalchemy as sa
from sqlalchemy.orm import relationship

from source.db.db import Base


class Shop(Base):
    __tablename__ = 'shops'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    supplier = sa.Column(sa.String)

    api_token_standard = sa.Column(sa.String)
    api_token_advertisement = sa.Column(sa.String)
    api_token_statistic = sa.Column(sa.String)

    is_active = sa.Column(sa.Boolean, unique=False)

    products = relationship('Product', back_populates='shop')
    history = relationship('ProductHistory', back_populates='shop')
    orders = relationship('Order', back_populates='shop')

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Product(Base):
    __tablename__ = 'products'

    id = sa.Column(sa.Integer, primary_key=True)
    nm_id = sa.Column(sa.BIGINT)
    vendor_code = sa.Column(sa.String)
    brand = sa.Column(sa.String)
    subj_name = sa.Column(sa.String)
    subj_root_name = sa.Column(sa.String)
    imt_name = sa.Column(sa.String)
    name = sa.Column(sa.String)
    description = sa.Column(sa.String)

    priceU = sa.Column(sa.Integer)
    salePriceU = sa.Column(sa.Integer)
    clientSale = sa.Column(sa.Integer)
    basicSale = sa.Column(sa.Integer)
    updated_at = sa.Column(sa.DateTime)

    shops_supplier = sa.Column(sa.String)
    shop_id = sa.Column(sa.Integer, sa.ForeignKey('shops.id'))
    shop = relationship('Shop', back_populates='products')

    def __str__(self):
        return str(self.nm_id)

    def __repr__(self):
        return str(self.nm_id)


class Characteristic(Base):
    __tablename__ = 'characteristics'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    value = sa.Column(sa.String)

    product_nm_id = sa.Column(sa.BIGINT)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class ProductHistory(Base):
    __tablename__ = 'product_histories'

    id = sa.Column(sa.Integer, primary_key=True)
    nm_id = sa.Column(sa.BIGINT)
    action = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime)

    shops_supplier = sa.Column(sa.String)
    shop_id = sa.Column(sa.Integer, sa.ForeignKey('shops.id'))
    shop = relationship('Shop', back_populates='history')

    def __str__(self):
        return str(self.nm_id)

    def __repr__(self):
        return str(self.nm_id)


class Order(Base):
    __tablename__ = 'orders'

    id = sa.Column(sa.Integer, primary_key=True)
    orderUid = sa.Column(sa.String)
    nm_id = sa.Column(sa.BIGINT)

    shop_id = sa.Column(sa.Integer, sa.ForeignKey('shops.id'))
    shop = relationship('Shop', back_populates='orders')

    def __str__(self):
        return f'{self.nm_id} order'

    def __repr__(self):
        return f'{self.nm_id} order'
