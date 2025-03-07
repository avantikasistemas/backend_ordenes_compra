from fastapi import APIRouter, Request # Depends
from Class.Parametros import Parametros
from Utils.decorator import http_decorator

parametros_router = APIRouter()

@parametros_router.post('/get_usuarios', tags=["Parametros"], response_model=dict)
@http_decorator
def get_usuarios(request: Request):
    response = Parametros().get_usuarios()
    return response
