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
