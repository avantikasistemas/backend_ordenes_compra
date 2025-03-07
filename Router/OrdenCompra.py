from fastapi import APIRouter, Request # Depends
from Schemas.OrdenCompra.get_orden_compra import GetOrdenCompra
from Class.OrdenCompra import OrdenCompra
from Utils.decorator import http_decorator

orden_compra_router = APIRouter()

@orden_compra_router.post('/get_orden_compra_data', tags=["Orden de Compra"], response_model=dict)
@http_decorator
def get_orden_compra_data(request: Request, get_orden_compra: GetOrdenCompra):
    data = getattr(request.state, "json_data", {})
    response = OrdenCompra().get_orden_compra_data(data)
    return response

@orden_compra_router.post('/generar_excel', tags=["Orden de Compra"], response_model=dict)
@http_decorator
def generar_excel(request: Request):
    data = getattr(request.state, "json_data", {})
    response = OrdenCompra().generar_excel(data)
    return response

@orden_compra_router.post('/guardar_registro_estado_oc', tags=["Orden de Compra"], response_model=dict)
@http_decorator
def guardar_registro_estado_oc(request: Request):
    data = getattr(request.state, "json_data", {})
    response = OrdenCompra().guardar_registro_estado_oc(data)
    return response
