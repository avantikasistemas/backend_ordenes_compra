from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from Config.db import BASE, engine
from Middleware.get_json import JSONMiddleware
from Router.OrdenCompra import orden_compra_router
from Router.Parametros import parametros_router
from Router.OrdenCompraNacional import orden_compra_router_nacional
from Router.Seguimiento import seguimiento_router
from Router.Anulacion import anular_router

app = FastAPI()
app.title = "Avantika Ordenes de Compra"
app.version = "0.0.1"

app.add_middleware(JSONMiddleware)
app.add_middleware(
    CORSMiddleware,allow_origins=["*"],  # Permitir todos los orígenes; para producción, especifica los orígenes permitidos.
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos; puedes especificar los métodos permitidos.
    allow_headers=["*"],  # Permitir todos los encabezados; puedes especificar los encabezados permitidos.
)
app.include_router(orden_compra_router)
app.include_router(parametros_router)
app.include_router(orden_compra_router_nacional)
app.include_router(seguimiento_router)
app.include_router(anular_router)

BASE.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
