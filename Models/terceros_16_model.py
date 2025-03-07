from Config.db import BASE
from sqlalchemy import Column, String

class Terceros16Model(BASE):

    __tablename__= "terceros_16"
    
    concepto_16 = Column(String, nullable=True)
    descripcion = Column(String, nullable=True)
    exportado = Column(String, nullable=True)
    activo = Column(String, nullable=True)
