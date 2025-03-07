from typing import Optional
from pydantic import BaseModel

class GetOrdenCompra(BaseModel):
    oc: Optional[str] = None
    fecha_oc_desde: Optional[str] = None
    fecha_oc_hasta: Optional[str] = None
    solicitud_aprobacion: Optional[str] = None
    usuario: Optional[str] = None
    enviada_proveedor: Optional[str] = None
    confirmada_proveedor: Optional[str] = None
