from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Schemas.OrdenCompra.get_orden_compra import GetOrdenCompra
from Class.Anulacion import Anulacion
from Utils.decorator import http_decorator
from Config.db import get_db
import socket

anular_router = APIRouter()

@anular_router.post('/peticion_anular_orden_compra', tags=["Orden de Compra"], response_model=dict)
@http_decorator
def peticion_anular_orden_compra(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Anulacion(db).peticion_anular_orden_compra(data)
    return response

@anular_router.post('/validar_anulacion_orden_compra', tags=["Orden de Compra"], response_model=dict)
@http_decorator
def validar_anulacion_orden_compra(request: Request, db: Session = Depends(get_db)):
    ip = request.client.host
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except Exception:
        hostname = None
    data = getattr(request.state, "json_data", {})
    response = Anulacion(db).validar_anulacion_orden_compra(data, ip, hostname)
    return response
