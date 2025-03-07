from Config.db import BASE
from sqlalchemy import Column, String

class Terceros2Model(BASE):

    __tablename__= "terceros_2"
    
    concepto_2 = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    exportado = Column(String, nullable=True)
    cuota = Column(String, nullable=True)
    correo = Column(String, nullable=True)
    correo_ejec = Column(String, nullable=True)
    activo = Column(String, nullable=True)
    icono = Column(String, nullable=True)
    Linea = Column(String, nullable=True)
