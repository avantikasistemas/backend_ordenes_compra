from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Class.OrdenCompraNacional import OrdenCompraNacional
from Utils.decorator import http_decorator
from Config.db import get_db

orden_compra_router_nacional = APIRouter()

@orden_compra_router_nacional.post('/buscar_oc_nacional', tags=["Orden de Compra Nacional"], response_model=dict)
@http_decorator
def buscar_oc_nacional(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = OrdenCompraNacional(db).buscar_oc_nacional(data)
    return response

@orden_compra_router_nacional.post('/solicitar_autorizacion', tags=["Orden de Compra Nacional"], response_model=dict)
@http_decorator
def solicitar_autorizacion(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = OrdenCompraNacional(db).solicitar_autorizacion(data)
    return response

@orden_compra_router_nacional.post('/obtener_detalle_kit', tags=["Orden de Compra Nacional"], response_model=dict)
@http_decorator
def obtener_detalle_kit(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = OrdenCompraNacional(db).obtener_detalle_kit(data)
    return response

@orden_compra_router_nacional.post('/autorizar_oc', tags=["Orden de Compra Nacional"], response_model=dict)
@http_decorator
def autorizar_oc(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    data["client_ip"] = request.client.host
    response = OrdenCompraNacional(db).autorizar_oc(data)
    return response
