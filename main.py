from fastapi import FastAPI
from source.core.routes import router as main_router
from sqladmin import Admin
import uvicorn

from source.db.db import async_engine
from source.product_management.admin import ProductAdmin, ProductHistoryAdmin, CharacteristicAdmin, ShopAdmin, \
    OrderAdmin

app = FastAPI(title='Мониторинг товаров WB')
app.include_router(router=main_router)


admin = Admin(app=app, engine=async_engine)

admin.add_view(view=ShopAdmin)
admin.add_view(view=ProductAdmin)
admin.add_view(view=CharacteristicAdmin)
admin.add_view(view=ProductHistoryAdmin)
admin.add_view(view=OrderAdmin)


if __name__ == '__main__':
    uvicorn.run(
        app='main:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
