
from Config.db import session
from Utils.tools import Tools, CustomException
from sqlalchemy import text

class Querys:

    def __init__(self):
        self.tools = Tools()
        self.query_params = dict()

    # Query para obtener los tipos de estado para la cotizacion
    def get_usuarios(self):

        try:
            response = list()
            sql = """
                SELECT DISTINCT u.des_usuario, dph.usuario AS creador_oc
                FROM dbo.documentos_ped_historia AS dph
                INNER JOIN dbo.usuarios AS u ON dph.usuario = u.usuario
                WHERE dph.sw = 3
                AND dph.fecha BETWEEN '20241101' AND '20501231'
                AND dph.bodega <> 99
                ORDER BY u.des_usuario;
            """

            query = session.execute(text(sql)).fetchall()
            if query:
                for key in query:
                    response.append({
                        "des_usuario": key[0].upper(),
                        "usuario": key[1]
                    })

            return response
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            session.close()

    # Query para consultar la orden de compra segun un filtro
    def consultar_orden_compra(self, data: dict):

        try:
            oc = data["oc"]
            fecha_oc_desde = data["fecha_oc_desde"]
            fecha_oc_hasta = data["fecha_oc_hasta"]
            solicitud_aprobacion = data["solicitud_aprobacion"]
            usuario = data["usuario"]
            enviada_proveedor = data["enviada_proveedor"]
            confirmada_proveedor = data["confirmada_proveedor"]

            if solicitud_aprobacion:
                if solicitud_aprobacion == "1":
                    solicitud_aprobacion = "S"
                elif solicitud_aprobacion == "0":
                    solicitud_aprobacion = "N"

            response = list()
            
            sql = """
                WITH AutorizacionUltima AS (
                    SELECT
                        numero,
                        sw,
                        autorizacion,
                        ROW_NUMBER() OVER (
                            PARTITION BY numero, sw
                            ORDER BY fecha DESC -- Tomar el registro más reciente
                        ) AS rn
                    FROM Distru_Autorizacion_Compra
                )
                SELECT
                    dph."fecha" AS "fecha_orden_compra",
                    dph."nit",
                    t."nombres" AS proveedor,
                    dph."numero",
                    CASE
                        WHEN (SELECT anulado FROM documentos_ped WHERE numero = dph."numero" AND sw = dph."sw") = 1 THEN 'ANULADA'
                        ELSE 'VIGENTE'
                    END AS estado,
                    dph.usuario AS creador_oc,
                    CASE
                        WHEN au.autorizacion = 'S' THEN 'SI'
                        WHEN au.autorizacion = 'N' THEN 'NO'
                        ELSE ''
                    END AS autorizada,
                    dph."bodega" AS bodega,
                    reo.aprobada AS "aprobada",
                    reo.enviada_a_aprobar AS "enviada_a_aprobar",
                    reo.enviada_al_proveedor AS "enviada_a_proveedor",
                    reo.confirmada_por_proveedor AS "confirmada_por_proveedor?",
                    reo.fecha_envio_al_proveedor AS "fecha_envio_proveedor",
                    reo.observaciones AS "observaciones"
                FROM
                    documentos_ped_historia dph
                INNER JOIN
                    terceros t ON dph."nit" = t."nit"
                LEFT JOIN  
                    AutorizacionUltima au ON dph."numero" = au.numero AND dph."sw" = au.sw AND au.rn = 1
                LEFT JOIN
                    registro_estados_oc reo ON dph."numero" = reo.numero_oc  
                WHERE
                    dph.sw = 3
            """

            if oc:
                sql = self.add_oc_query(sql, oc)
            if fecha_oc_desde and fecha_oc_hasta:
                sql = self.add_fecha_oc_query(
                    sql, 
                    fecha_oc_desde, 
                    fecha_oc_hasta
                )
            if solicitud_aprobacion:
                sql = self.add_solicitud_aprobacion_query(
                    sql, 
                    solicitud_aprobacion
                )
            if usuario:
                sql = self.add_usuario_query(sql, usuario)
            if enviada_proveedor:
                sql = self.add_enviada_proveedor_query(
                    sql, 
                    enviada_proveedor
                )
            if confirmada_proveedor:
                sql = self.add_confirmada_proveedor_query(
                    sql, 
                    confirmada_proveedor
                )
            sql = sql + " ORDER BY dph.fecha DESC;"

            if self.query_params:
                query = session.execute(text(sql), self.query_params).fetchall()
            else:
                query = session.execute(text(sql)).fetchall()

            if query:
                for index, key in enumerate(query):
                    aprobada = ''
                    enviada_a_aprobar = ''
                    enviada_a_proveedor = ''
                    confirmada_por_proveedor = ''
                    if key[8] == 1:
                        aprobada = 'SI'
                    elif key[8] == 0:
                        aprobada = 'NO'
                    if key[9] == 1:
                        enviada_a_aprobar = 'SI'
                    elif key[9] == 0:
                        enviada_a_aprobar = 'NO'
                    if key[10] == 1:
                        enviada_a_proveedor = 'SI'
                    elif key[10] == 0:
                        enviada_a_proveedor = 'NO'
                    if key[11] == 1:
                        confirmada_por_proveedor = 'SI'
                    elif key[11] == 0:
                        confirmada_por_proveedor = 'NO'
                    response.append({
                        "consecutivo": index + 1,
                        "fecha_orden_compra": self.tools.format_date(str(key[0]), "%Y-%m-%d %H:%M:%S", "%Y-%m-%d")  if key[0] else '',
                        "nit": key[1],
                        "proveedor": key[2],
                        "numero": key[3],
                        "estado": key[4],
                        "creador_oc": key[5],
                        "autorizada": key[6],
                        "bodega": key[7],
                        "aprobada": key[8],
                        "aprobada?": aprobada,
                        "enviada_a_aprobar": key[9],
                        "enviada_a_aprobar?": enviada_a_aprobar,
                        "enviada_a_proveedor": key[10],
                        "enviada_a_proveedor?": enviada_a_proveedor,
                        "confirmada_por_proveedor": key[11],
                        "confirmada_por_proveedor?": confirmada_por_proveedor,
                        "fecha_envio_proveedor": key[12],
                        "observaciones": key[13]
                    })

            return response
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            session.close()

    def add_oc_query(self, sql, oc):
        sql = sql + " AND dph.numero = :oc"
        self.query_params.update({"oc": oc})
        return sql

    def add_fecha_oc_query(self, sql, fecha_desde, fecha_hasta):
        sql = sql + " AND dph.fecha BETWEEN :fecha_desde AND :fecha_hasta"
        self.query_params.update({"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta})
        return sql

    def add_solicitud_aprobacion_query(self, sql, solicitud_aprobacion):
        sql = sql + " AND au.autorizacion = :solicitud_aprobacion"
        self.query_params.update({"solicitud_aprobacion": solicitud_aprobacion})
        return sql

    def add_usuario_query(self, sql, usuario):
        sql = sql + " AND dph.usuario = :usuario"
        self.query_params.update({"usuario": usuario})
        return sql

    def add_enviada_proveedor_query(self, sql, enviada_proveedor):
        sql = sql + " AND reo.enviada_al_proveedor = :enviado"
        self.query_params.update({"enviado": enviada_proveedor})
        return sql

    def add_confirmada_proveedor_query(self, sql, confirmada_proveedor):
        sql = sql + " AND reo.confirmada_por_proveedor = :confirmado"
        self.query_params.update({"confirmado": confirmada_proveedor})
        return sql

    def guardar_registro_estado_oc(self, data: dict):

        try:
            sql_search = """
                SELECT * FROM dbo.registro_estados_oc WHERE numero_oc = :oc;
            """ 
            result = session.execute(text(sql_search), {"oc": data["oc"]}).fetchone()
            if not result:
                sql = """
                    INSERT INTO dbo.registro_estados_oc (
                        numero_oc, enviada_a_aprobar, enviada_al_proveedor, 
                        confirmada_por_proveedor, fecha_envio_al_proveedor,
                        observaciones
                    )
                    VALUES (
                        :oc, :enviada_a_aprobar, :enviada_al_proveedor, 
                        :confirmada_por_proveedor, :fecha_envio_al_proveedor, 
                        :observaciones
                    )
                """
                query = session.execute(text(sql), data)
                session.commit()
                if not query:
                    msg = """ 
                        Problemas al guardar registro, por favor contacte con 
                        el administrador.
                    """
                    raise CustomException(msg)
                return True
        
            registro_id = result[0]
            numero_oc = result[1]
            print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            if data["oc"] != numero_oc:
                msg = "El número de orden de compra a actualizar no coincide."
                raise CustomException(msg)
            
            print("bbbbbbbbbbbbbbbbbbbbbbbbbbbb")
            print(data)
            
            data_update = {
                "registro_id": registro_id,
                "oc": numero_oc,
                "enviada_a_aprobar": data["enviada_a_aprobar"],
                "enviada_al_proveedor": data["enviada_al_proveedor"],
                "confirmada_por_proveedor": data["confirmada_por_proveedor"],
                "fecha_envio_al_proveedor": data["fecha_envio_al_proveedor"],
                "observaciones": data["observaciones"],
            }
            print(data_update)
            sql_update = """
                UPDATE dbo.registro_estados_oc SET enviada_a_aprobar = :enviada_a_aprobar,
                enviada_al_proveedor = :enviada_al_proveedor, 
                confirmada_por_proveedor = :confirmada_por_proveedor, 
                fecha_envio_al_proveedor = :fecha_envio_al_proveedor,
                observaciones = :observaciones
                WHERE id = :registro_id AND numero_oc = :oc;
            """
            query_update = session.execute(text(sql_update), data_update)
            session.commit()
            if not query_update:
                msg = """ 
                    Problemas al guardar registro, por favor contacte con 
                    el administrador.
                """
                raise CustomException(msg)
            return True
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            session.close()
