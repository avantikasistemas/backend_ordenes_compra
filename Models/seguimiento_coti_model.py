from Config.db import BASE
from sqlalchemy import Column, String, BigInteger, Text, Integer, DateTime, DECIMAL, Date

class SeguimientoCotiModel(BASE):

    __tablename__= "seguimiento_coti"
    
    id = Column(BigInteger, primary_key=True)
    email_sender = Column(String, nullable=False)
    email_subject = Column(String, nullable=True)
    email_datetime = Column(DateTime(), nullable=True)
    nit = Column(String, nullable=True)
    nombre = Column(String, nullable=False)
    coordinador = Column(String, nullable=True)
    ejecutivo = Column(String, nullable=False)
    tipo_cliente = Column(String, nullable=True)
    zona = Column(String, nullable=True)
    fecha_vencimiento = Column(DateTime(), nullable=True)
    numero_cotizacion = Column(String, nullable=True)
    estado = Column(String, nullable=True)
    cotizacion_concepto = Column(String, nullable=True)
    fecha_entrega = Column(DateTime(), nullable=True)
    usuario_creador_cotizacion = Column(String, nullable=True)
    pesos_cotizados = Column(DECIMAL, nullable=True)
    items_cotizados = Column(Integer, nullable=True)
    oportunidad_entrega = Column(String, nullable=True)
    dias_entrega = Column(Integer, nullable=True)
    items_a_cotizar = Column(String, nullable=True)
    seguimiento_usuario = Column(String, nullable=True)
    seguimiento_actividad = Column(String, nullable=True)
    seguimiento_resultado = Column(String, nullable=True)
    seguimiento_comentario = Column(Text)
    seguimiento_fecha_creacion = Column(DateTime(), nullable=True)
    nueva_fecha_vencimiento = Column(Date, nullable=True)
    motivo_no_cotizacion = Column(String, nullable=True)
    desvio_oportunidad = Column(String, nullable=True)
    item_revisado_cumple = Column(Integer, default=0, nullable=True)
    item_revisado_muestra = Column(Integer, default=0, nullable=True)
    porcentaje_muestra = Column(Integer, default=0, nullable=True)
    desvio_calidad = Column(String, nullable=True)
    
    def __init__(self, data: dict):
        self.email_sender = data['email_sender']
        self.email_subject = data['email_subject']
        self.email_datetime = data['email_datetime']
        self.nit = data['nit']
        self.nombre = data['nombre']
        self.coordinador = data['coordinador']
        self.ejecutivo = data['ejecutivo']
        self.tipo_cliente = data['tipo_cliente']
        self.zona = data['zona']
        self.fecha_vencimiento = data['fecha_vencimiento']
        self.numero_cotizacion = data['numero_cotizacion']
        self.estado = data['estado']
        self.cotizacion_concepto = data['cotizacion_concepto']
        self.fecha_entrega = data['fecha_entrega']
        self.usuario_creador_cotizacion = data['usuario_creador_cotizacion']
        self.pesos_cotizados = data['pesos_cotizados']
        self.items_cotizados = data['items_cotizados']
        self.oportunidad_entrega = data['oportunidad_entrega']
        self.dias_entrega = data['dias_entrega']
        self.items_a_cotizar = data['items_a_cotizar']
        self.nueva_fecha_vencimiento = data['nueva_fecha_vencimiento']
        self.motivo_no_cotizacion = data['motivo_no_cotizacion']
        self.desvio_oportunidad = data['desvio_oportunidad']
        self.item_revisado_cumple = data['item_revisado_cumple']
        self.item_revisado_muestra = data['item_revisado_muestra']
        self.porcentaje_muestra = data['porcentaje_muestra']
        self.desvio_calidad = data['desvio_calidad']
