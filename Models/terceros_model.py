from Config.db import BASE
from sqlalchemy import Column, String, Text, Integer, DateTime, DECIMAL

class TercerosModel(BASE):

    __tablename__= "terceros"
    
    # nit = Column(DECIMAL(18, 0), nullable=False)
    nit = Column(DECIMAL(18, 0), nullable=False)
    digito = Column(Integer, nullable=True)
    nombres = Column(String, nullable=False)
    direccion = Column(String, nullable=True)
    ciudad = Column(String, nullable=True)
    telefono_1 = Column(String, nullable=True)
    telefono_2 = Column(String, nullable=True)
    fax = Column(String, nullable=True)
    apartado_aereo = Column(String, nullable=True)
    tipo_identificacion = Column(String, nullable=True)
    pais = Column(String, nullable=True)
    gran_contribuyente = Column(Integer, nullable=False)
    autoretenedor = Column(Integer, nullable=False)
    bloqueo = Column(Integer, nullable=True)
    notas = Column(Text, nullable=True)
    lista = Column(Integer, nullable=True)
    concepto_1 = Column(String, nullable=True)
    concepto_2 = Column(String, nullable=True)
    concepto_3 = Column(String, nullable=True)
    concepto_4 = Column(String, nullable=True)
    concepto_5 = Column(String, nullable=True)
    concepto_6 = Column(String, nullable=True)
    concepto_7 = Column(String, nullable=True)
    concepto_8 = Column(String, nullable=True)
    concepto_9 = Column(String, nullable=True)
    concepto_10 = Column(String, nullable=True)
    mail = Column(Text, nullable=True)
    pos_num = Column(Integer, nullable=False)
    regimen = Column(String, nullable=True)
    cupo_credito = Column(DECIMAL, nullable=True)
    nit_real = Column(DECIMAL(18, 0), nullable=False)
    condicion = Column(String, nullable=True)
    vendedor = Column(DECIMAL(18, 0), nullable=True)
    fletes = Column(DECIMAL, nullable=True)
    es_excento_iva = Column(String, nullable=True)
    contacto_1 = Column(String, nullable=True)
    contacto_2 = Column(String, nullable=True)
    formato_factura = Column(String, nullable=True)
    fecha_creacion = Column(DateTime(), nullable=True)
    formato_copias = Column(Integer, nullable=True)
    tipo_factura = Column(String, nullable=True)
    dias_gracia = Column(Integer, nullable=True)
    solo_contado = Column(String, nullable=True)
    descuento_fijo = Column(DECIMAL, nullable=True)
    excluir_tabla_desc = Column(String, nullable=True)
    centro_fijo = Column(Integer, nullable=True)
    exportado = Column(String, nullable=True)
    factor_o_lista = Column(String, nullable=True)
    codigo_ica = Column(Integer, nullable=True)
    y_dpto = Column(String, nullable=True)
    y_ciudad = Column(String, nullable=True)
    celular = Column(String, nullable=True)
    barrio = Column(String, nullable=True)
    ean = Column(String, nullable=True)
    lista2 = Column(Integer, nullable=True)
    id = Column(Integer, nullable=True)
    clasificado = Column(String, nullable=True)
    id_Tipo_Tercero = Column(Integer, nullable=True)
    vender_controlados = Column(String, nullable=True)
    estampilla = Column(DECIMAL, nullable=True)
    timbre = Column(DECIMAL, nullable=True)
    impdeporte = Column(DECIMAL, nullable=True)
    impica = Column(DECIMAL, nullable=True)
    impconsumo = Column(DECIMAL, nullable=True)
    codigo_alterno = Column(String, nullable=True)
    tipo_devolucion = Column(String, nullable=True)
    Usuario = Column(String, nullable=True)
    Motivo_Estado = Column(String, nullable=True)
    y_pais = Column(String, nullable=True)
    ext_1 = Column(String, nullable=True)
    tipo_direccion = Column(Integer, nullable=True)
    concepto_11 = Column(String, nullable=True)
    concepto_12 = Column(String, nullable=True)
    concepto_13 = Column(String, nullable=True)
    concepto_14 = Column(String, nullable=True)
    concepto_15 = Column(String, nullable=True)
    concepto_16 = Column(String, nullable=True)
    concepto_17 = Column(String, nullable=True)
    concepto_18 = Column(String, nullable=True)
    concepto_19 = Column(String, nullable=True)
    concepto_20 = Column(String, nullable=True)
    Separa_Iva = Column(Integer, nullable=True)
    Separa_Negocio = Column(Integer, nullable=True)
    Solo_Remision = Column(Integer, nullable=True)
    Devolver_Prod = Column(Integer, nullable=True)
    GLN_Cabasnet = Column(String, nullable=True)
    otro_descuento = Column(DECIMAL, nullable=True)
    no_regulados = Column(String, nullable=True)
    id_definicion_tributaria_tipo = Column(Integer, nullable=True)
    dias_recibo_caja = Column(Integer, nullable=True)
    estado_civil = Column(String, nullable=True)
    estrato = Column(String, nullable=True)
    paginaweb = Column(String, nullable=True)
    area_labora = Column(String, nullable=True)
    cargo = Column(String, nullable=True)
    ext2 = Column(String, nullable=True)
    celular2 = Column(String, nullable=True)
    email2 = Column(String, nullable=True)
    descuento_financiero = Column(DECIMAL, nullable=True)
    actividad_cree = Column(String, nullable=True)
    autoretenedorica = Column(Integer, nullable=True)
    es_excento_cree_ventas = Column(String, nullable=True)
    sincronizado = Column(String, nullable=True)
    minimo_ret_vtas = Column(DECIMAL, nullable=True)
    formatoRemision = Column(String, nullable=True)
    tieneRUT = Column(String, nullable=True)
    codigoActividadEconomica = Column(String, nullable=True)
    mail_adicional = Column(String, nullable=True)
    codigoPostal = Column(String, nullable=True)
    ftoCopia_factura = Column(String, nullable=True)
    copiaRemision = Column(String, nullable=True)
    fecha_cambio_razon = Column(DateTime(), nullable=True)
    razon_comercial = Column(String, nullable=True)
    departamento = Column(String, nullable=True)
    ciudad2 = Column(String, nullable=True)
    es_electronico = Column(String, nullable=True)
    CodigoPostalDir = Column(String, nullable=True)
    fecha_inicio_FE = Column(DateTime(), nullable=True)
    soporte_DIAN = Column(String, nullable=True)
    tributo = Column(String, nullable=True)
    es_proveedor = Column(Integer, nullable=True)
    Runt = Column(String, nullable=True)
    Fecha_Runt = Column(DateTime(), nullable=True)
