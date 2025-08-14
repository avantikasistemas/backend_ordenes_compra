from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Schemas.OrdenCompra.get_orden_compra import GetOrdenCompra
from Class.Seguimiento import Seguimiento
from Utils.decorator import http_decorator
from Config.db import get_db

seguimiento_router = APIRouter()

@seguimiento_router.post('/guardar_seguimiento', tags=["Orden de Compra"], response_model=dict)
@http_decorator
def guardar_seguimiento(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Seguimiento(db).guardar_seguimiento(data)
    return response

@seguimiento_router.post('/cargar_datos_seguimiento', tags=["Orden de Compra"], response_model=dict)
@http_decorator
def cargar_datos_seguimiento(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Seguimiento(db).cargar_datos_seguimiento(data)
    return response
