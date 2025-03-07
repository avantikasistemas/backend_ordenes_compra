from Config.db import BASE
from sqlalchemy import Column, String

class TercerosVentasModel(BASE):

    __tablename__= "terceros_ventas"
    
    concepto_2 = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    activo = Column(String, nullable=True)
    linea = Column(String, nullable=True)
    coodinacion = Column(String, nullable=True)
    nit_coord = Column(String, nullable=True)
    coordinador = Column(String, nullable=True)
    correo_coord = Column(String, nullable=True)
    cel_coord = Column(String, nullable=True)
    ext_coord = Column(String, nullable=True)
    nit_ejecutivo = Column(String, nullable=True)
    ejecutivo = Column(String, nullable=True)
    correo_ejec = Column(String, nullable=True)
    cel_ejec = Column(String, nullable=True)
    ext_ejec = Column(String, nullable=True)
