from Utils.tools import Tools, CustomException
from sqlalchemy import text
from datetime import datetime
from typing import Dict, Any, List, Tuple, Set

class Querys:

    def __init__(self, db):
        self.db = db
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

            query = self.db.execute(text(sql)).fetchall()
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
            self.db.close()

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
            estado_orden = data["estado_orden"]
            enviada_a_aprobar = data["enviada_a_aprobar"]
            cant_registros = 0
            limit = data["limit"]
            position = data["position"]

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
                    COALESCE(reo.aprobada, 0) AS "aprobada",
                    COALESCE(reo.enviada_a_aprobar, 0) AS "enviada_a_aprobar",
                    COALESCE(reo.enviada_al_proveedor, 0) AS "enviada_a_proveedor",
                    COALESCE(reo.confirmada_por_proveedor, 0) AS "confirmada_por_proveedor?",
                    reo.fecha_envio_al_proveedor AS "fecha_envio_proveedor",
                    reo.observaciones AS "observaciones",
                    COUNT(*) OVER() AS total_registros
                FROM
                    documentos_ped_historia dph
                INNER JOIN
                    terceros t ON dph."nit" = t."nit"
                LEFT JOIN  
                    AutorizacionUltima au ON dph."numero" = au.numero AND dph."sw" = au.sw AND au.rn = 1
                LEFT JOIN
                    dbo.registro_estados_oc reo ON dph."numero" = reo.numero_oc  
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
            if estado_orden:
                sql = self.add_estado_query(
                    sql, 
                    estado_orden
                )
            if enviada_a_aprobar:
                sql = self.add_enviada_a_aprobar_query(
                    sql, 
                    enviada_a_aprobar
                )
            
            new_offset = self.obtener_limit(limit, position)
            self.query_params.update({"offset": new_offset, "limit": limit})
            sql = sql + " ORDER BY dph.numero DESC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;"

            if self.query_params:
                query = self.db.execute(text(sql), self.query_params).fetchall()
            else:
                query = self.db.execute(text(sql)).fetchall()

            if query:
                cant_registros = query[0][14]
                for index, key in enumerate(query):
                    reo_aprobada = key[8]
                    reo_enviada_a_aprobar = key[9]
                    reo_enviada_a_proveedor = key[10]
                    reo_confirmada_por_proveedor = key[11]
                    if reo_aprobada == 1:
                        aprobada_texto = 'SI'
                    elif reo_aprobada == 0:
                        aprobada_texto = 'NO'
                    if reo_enviada_a_aprobar == 1:
                        enviada_a_aprobar_texto = 'SI'
                    elif reo_enviada_a_aprobar == 0:
                        enviada_a_aprobar_texto = 'NO'
                    if reo_enviada_a_proveedor == 1:
                        enviada_a_proveedor_texto = 'SI'
                    elif reo_enviada_a_proveedor == 0:
                        enviada_a_proveedor_texto = 'NO'
                    if reo_confirmada_por_proveedor == 1:
                        confirmada_por_proveedor_texto = 'SI'
                    elif reo_confirmada_por_proveedor == 0:
                        confirmada_por_proveedor_texto = 'NO'
                        
                    numero = key[3]
                    autorizada = key[6]

                    if autorizada == "SI" and reo_aprobada == 0:
                        nuevo_registro = self.registrar_aprobacion_oc(numero)
                        if nuevo_registro:
                            # Aquí puedes reasignar lo que necesites
                            aprobada_texto = 'NO'
                            enviada_a_aprobar_texto = 'NO'
                            enviada_a_proveedor_texto = 'NO'
                            confirmada_por_proveedor_texto = 'NO'
                            
                            reo_aprobada = nuevo_registro.get("aprobada", 0)
                            reo_enviada_a_aprobar = nuevo_registro.get("enviada_a_aprobar", 0)
                            reo_enviada_a_proveedor = nuevo_registro.get("enviada_a_proveedor", 0)
                            reo_confirmada_por_proveedor = nuevo_registro.get("confirmada_por_proveedor", 0)
                            
                            if reo_aprobada != 0:
                                aprobada_texto = 'SI'
                            if reo_enviada_a_aprobar != 0:
                                enviada_a_aprobar_texto = 'SI'
                            if reo_enviada_a_proveedor != 0:
                                enviada_a_proveedor_texto = 'SI'
                            if reo_confirmada_por_proveedor != 0:
                                confirmada_por_proveedor_texto = 'SI'
                            
                    if autorizada == "SI" and reo_aprobada == 1 and reo_enviada_a_aprobar == 0:
                        nuevo_registro = self.registrar_aprobacion_oc(numero)
                        if nuevo_registro:
                            # Aquí puedes reasignar lo que necesites
                            aprobada_texto = 'NO'
                            enviada_a_aprobar_texto = 'NO'
                            enviada_a_proveedor_texto = 'NO'
                            confirmada_por_proveedor_texto = 'NO'
                            
                            reo_aprobada = nuevo_registro.get("aprobada", 0)
                            reo_enviada_a_aprobar = nuevo_registro.get("enviada_a_aprobar", 0)
                            reo_enviada_a_proveedor = nuevo_registro.get("enviada_a_proveedor", 0)
                            reo_confirmada_por_proveedor = nuevo_registro.get("confirmada_por_proveedor", 0)
                            
                            if reo_aprobada != 0:
                                aprobada_texto = 'SI'
                            if reo_enviada_a_aprobar != 0:
                                enviada_a_aprobar_texto = 'SI'
                            if reo_enviada_a_proveedor != 0:
                                enviada_a_proveedor_texto = 'SI'
                            if reo_confirmada_por_proveedor != 0:
                                confirmada_por_proveedor_texto = 'SI'
                    
                    response.append({
                        "consecutivo": index + 1,
                        "fecha_orden_compra": self.tools.format_date(str(key[0]), "%Y-%m-%d %H:%M:%S", "%d-%b-%Y")  if key[0] else '',
                        "nit": key[1],
                        "proveedor": key[2],
                        "numero": numero,
                        "estado": key[4],
                        "creador_oc": key[5],
                        "autorizada": autorizada,
                        "bodega": key[7],
                        "aprobada": reo_aprobada,
                        "aprobada?": aprobada_texto,
                        "enviada_a_aprobar": reo_enviada_a_aprobar,
                        "enviada_a_aprobar?": enviada_a_aprobar_texto,
                        "enviada_a_proveedor": reo_enviada_a_proveedor,
                        "enviada_a_proveedor?": enviada_a_proveedor_texto,
                        "confirmada_por_proveedor": reo_confirmada_por_proveedor,
                        "confirmada_por_proveedor?": confirmada_por_proveedor_texto,
                        "fecha_envio_proveedor": key[12],
                        "observaciones": key[13]
                    })
            result = {"registros": response, "cant_registros": cant_registros}
            return result
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para consultar la orden de compra segun un filtro
    def consultar_orden_compra_excel(self, data: dict):

        try:
            oc = data["oc"]
            fecha_oc_desde = data["fecha_oc_desde"]
            fecha_oc_hasta = data["fecha_oc_hasta"]
            solicitud_aprobacion = data["solicitud_aprobacion"]
            usuario = data["usuario"]
            enviada_proveedor = data["enviada_proveedor"]
            confirmada_proveedor = data["confirmada_proveedor"]
            estado_orden = data["estado_orden"]
            enviada_a_aprobar = data["enviada_a_aprobar"]

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
                    COALESCE(reo.aprobada, 0) AS "aprobada",
                    COALESCE(reo.enviada_a_aprobar, 0) AS "enviada_a_aprobar",
                    COALESCE(reo.enviada_al_proveedor, 0) AS "enviada_a_proveedor",
                    COALESCE(reo.confirmada_por_proveedor, 0) AS "confirmada_por_proveedor?",
                    reo.fecha_envio_al_proveedor AS "fecha_envio_proveedor",
                    reo.observaciones AS "observaciones"
                FROM
                    documentos_ped_historia dph
                INNER JOIN
                    terceros t ON dph."nit" = t."nit"
                LEFT JOIN  
                    AutorizacionUltima au ON dph."numero" = au.numero AND dph."sw" = au.sw AND au.rn = 1
                LEFT JOIN
                    dbo.registro_estados_oc reo ON dph."numero" = reo.numero_oc  
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
            if estado_orden:
                sql = self.add_estado_query(
                    sql, 
                    estado_orden
                )
            if enviada_a_aprobar:
                sql = self.add_enviada_a_aprobar_query(
                    sql, 
                    enviada_a_aprobar
                )
            
            sql = sql + " ORDER BY dph.fecha DESC;"

            if self.query_params:
                query = self.db.execute(text(sql), self.query_params).fetchall()
            else:
                query = self.db.execute(text(sql)).fetchall()

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
                        "fecha_orden_compra": self.tools.format_date(str(key[0]), "%Y-%m-%d %H:%M:%S", "%d-%b-%Y")  if key[0] else '',
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
            self.db.close()

    # Query que complementa la inicial que busca la orden de compra
    def add_oc_query(self, sql, oc):
        sql = sql + " AND dph.numero = :oc"
        self.query_params.update({"oc": oc})
        return sql

    # Query que complementa la inicial que filtra por fechas
    def add_fecha_oc_query(self, sql, fecha_desde, fecha_hasta):
        sql = sql + " AND dph.fecha BETWEEN :fecha_desde AND :fecha_hasta"
        self.query_params.update({"fecha_desde": fecha_desde, "fecha_hasta": fecha_hasta})
        return sql

    # Query que complementa la inicial que filtra por solicitud de aprobación
    def add_solicitud_aprobacion_query(self, sql, solicitud_aprobacion):
        sql = sql + " AND au.autorizacion = :solicitud_aprobacion"
        self.query_params.update({"solicitud_aprobacion": solicitud_aprobacion})
        return sql

    # Query que complementa la inicial que filtra por nombre de usuario
    def add_usuario_query(self, sql, usuario):
        sql = sql + " AND dph.usuario = :usuario"
        self.query_params.update({"usuario": usuario})
        return sql

    # Query que complementa la inicial que filtra si fue enviada al proveedor
    def add_enviada_proveedor_query(self, sql, enviada_proveedor):
        sql = sql + " AND reo.enviada_al_proveedor = :enviado"
        self.query_params.update({"enviado": enviada_proveedor})
        return sql

    # Query que complementa la inicial que filtra si fue confirmada por proveedor
    def add_confirmada_proveedor_query(self, sql, confirmada_proveedor):
        sql = sql + " AND reo.confirmada_por_proveedor = :confirmado"
        self.query_params.update({"confirmado": confirmada_proveedor})
        return sql

    # Query que complementa la inicial que filtra por estado de la orden
    def add_estado_query(self, sql, estado_orden):
        sql = sql + " AND dph.anulado = :estado"
        self.query_params.update({"estado": estado_orden})
        return sql

    # Query que complementa la inicial que filtra si fue aprobada
    def add_enviada_a_aprobar_query(self, sql, enviada_a_aprobar):
        sql = sql + " AND reo.enviada_a_aprobar = :enviada_a_aprobar"
        self.query_params.update({"enviada_a_aprobar": enviada_a_aprobar})
        return sql

    # Función que arma el limite de paginación
    def obtener_limit(self, limit: int, position: int):
        offset = (position - 1) * limit
        return offset

    # Query que guarda las ordenes de compra
    def guardar_registro_estado_oc(self, data: dict):

        try:
            sql_search = """
                SELECT * FROM dbo.registro_estados_oc WHERE numero_oc = :oc;
            """ 
            result = self.db.execute(text(sql_search), {"oc": data["oc"]}).fetchone()
            if not result:
                sql = """
                    INSERT INTO dbo.registro_estados_oc (
                        numero_oc, aprobada, enviada_a_aprobar, 
                        enviada_al_proveedor, confirmada_por_proveedor,
                        fecha_envio_al_proveedor, observaciones
                    )
                    VALUES (
                        :oc, :aprobada, :enviada_a_aprobar, 
                        :enviada_al_proveedor, :confirmada_por_proveedor, 
                        :fecha_envio_al_proveedor, :observaciones
                    )
                """
                query = self.db.execute(text(sql), data)
                self.db.commit()
                if not query:
                    msg = """ 
                        Problemas al guardar registro, por favor contacte con 
                        el administrador.
                    """
                    raise CustomException(msg)
                return True
        
            registro_id = result[0]
            numero_oc = result[1]

            if data["oc"] != numero_oc:
                msg = "El número de orden de compra a actualizar no coincide."
                raise CustomException(msg)

            data_update = {
                "registro_id": registro_id,
                "oc": numero_oc,
                "aprobada": data["aprobada"],
                "enviada_a_aprobar": data["enviada_a_aprobar"],
                "enviada_al_proveedor": data["enviada_al_proveedor"],
                "confirmada_por_proveedor": data["confirmada_por_proveedor"],
                "fecha_envio_al_proveedor": data["fecha_envio_al_proveedor"] if data["fecha_envio_al_proveedor"] else None,
                "observaciones": data["observaciones"],
            }
            sql_update = """
                UPDATE dbo.registro_estados_oc SET aprobada = :aprobada, 
                enviada_a_aprobar = :enviada_a_aprobar,
                enviada_al_proveedor = :enviada_al_proveedor, 
                confirmada_por_proveedor = :confirmada_por_proveedor, 
                fecha_envio_al_proveedor = :fecha_envio_al_proveedor,
                observaciones = :observaciones
                WHERE id = :registro_id AND numero_oc = :oc;
            """
            query_update = self.db.execute(text(sql_update), data_update)
            self.db.commit()
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
            self.db.close()

    # Función que inserta o actualiza aprobado y enviado a aprobar
    # en caso que haya sido AUTORIZADA
    def registrar_aprobacion_oc(self, numero: int):
        try:
            # Verificar si ya existe
            consulta = self.db.execute(
                text("SELECT COUNT(1) FROM dbo.registro_estados_oc WHERE numero_oc = :numero"),
                {"numero": numero}
            ).scalar()

            if consulta and consulta > 0:
                # Si existe, actualizar
                self.db.execute(
                    text("""
                        UPDATE dbo.registro_estados_oc
                        SET aprobada = :aprobada, enviada_a_aprobar = :enviada_a_aprobar
                        WHERE numero_oc = :numero
                    """),
                    {"numero": numero, "aprobada": 1, "enviada_a_aprobar": 1}
                )
            else:
                # Si no existe, insertar
                self.db.execute(
                    text("""
                        INSERT INTO dbo.registro_estados_oc (numero_oc, aprobada, enviada_a_aprobar)
                        VALUES (:numero, :aprobada, :enviada_a_aprobar)
                    """),
                    {"numero": numero, "aprobada": 1, "enviada_a_aprobar": 1}
                )

            self.db.commit()

            # Retornar el registro actualizado o insertado
            registro = self.db.execute(
                text("SELECT * FROM dbo.registro_estados_oc WHERE numero_oc = :numero"),
                {"numero": numero}
            ).fetchone()

            return dict(registro._mapping) if registro else None

        except Exception as e:
            print(f"Error al consultar registros: {e}")
            self.db.rollback()
            raise CustomException("Error al consultar registros.")

    # Query que busca la orden de compra nacional
    def buscar_oc_nacional(self, oc, tasa, factor):

        try:
            sql = """
                SELECT m.descripcion as nombre_moneda, dph.*
                FROM documentos_ped_historia dph
                LEFT JOIN monedas m ON dph.moneda = m.moneda
                WHERE dph.sw = 3 AND numero = :oc AND anulado = 0
            """
            result = self.db.execute(text(sql), {"oc": oc}).fetchone()
            registros_dict = dict(result._mapping) if result else None

            # Retornamos la información.
            return registros_dict

        except Exception as e:
            print(f"Error al obtener información de orden de compra: {e}")
            raise CustomException("Error al obtener información de orden de compra.")

    # Query para guardar seguimiento
    def guardar_seguimiento(self, data: dict):
        try:
            self.db.execute(
                text("""
                    INSERT INTO dbo.seguimiento_ordenes_compra (numero, usuario, comentario)
                    VALUES (:numero, :usuario, :comentario)
                """),
                {
                    "numero": data["oc"],
                    "usuario": data["usuario"],
                    "comentario": data["comentario"]
                }
            )
            self.db.commit()
            return True
        except CustomException as e:
            print(f"Error al guardar seguimiento: {e}")
            self.db.rollback()
            raise CustomException("Error al guardar seguimiento.")
        finally:
            self.db.close()

    # Query para cargar datos de seguimiento
    def cargar_datos_seguimiento(self, oc):
        try:
            seguimientos = self.db.execute(
                text("""
                    SELECT * FROM dbo.seguimiento_ordenes_compra
                    WHERE numero = :numero AND estado = 1;
                """),
                {"numero": oc}
            ).fetchall()

            result = []
            for row in seguimientos:
                row_dict = dict(row._mapping)
                if "created_at" in row_dict and row_dict["created_at"]:
                    # Formatear el campo created_at
                    row_dict["created_at"] = row_dict["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                result.append(row_dict)
            return result if seguimientos else []
        except Exception as e:
            print(f"Error al cargar datos de seguimiento: {e}")
            raise CustomException("Error al cargar datos de seguimiento.")
        finally:
            self.db.close()

    # Query para verificar si la OC está anulada
    def check_si_oc_anulada(self, oc: int):
        try:
            sql = """
                SELECT t.nombres as tercero_nombre, dp.* FROM dbo.documentos_ped dp
                INNER JOIN terceros t ON dp.nit = t.nit
                WHERE dp.numero = :oc AND dp.sw = 3
            """
            result = self.db.execute(text(sql), {"oc": oc}).fetchone()
            result2_list = []
            if result:
                sql2 = """
                    SELECT r.descripcion as item_nombre, dlp.* FROM dbo.documentos_lin_ped dlp
                    INNER JOIN referencias r ON dlp.codigo = r.codigo
                    WHERE dlp.numero = :oc AND dlp.sw = 3
                """
                result2 = self.db.execute(text(sql2), {"oc": oc}).fetchall()
                if result2:
                    result2_list = [dict(row._mapping) for row in result2]
            if result:
                res_json = dict(result._mapping)
                res_json["oc_detalles"] = result2_list
                return res_json
            else:
                return None
        except Exception as e:
            print(f"Error al verificar si la OC está anulada: {e}")
            raise CustomException("Error al verificar si la OC está anulada.")

    # Query para guardar registro de anulación
    def guardar_registro_anulacion(self, data: dict):
        try:
            result = self.db.execute(
                text("""
                    INSERT INTO dbo.anulacion_ordenes_compra (numero, usuario, comentario, created_at)
                    OUTPUT INSERTED.*
                    VALUES (:numero, :usuario, :comentario, :created_at)
                """),
                {
                    "numero": data["oc"],
                    "usuario": data["usuario"],
                    "comentario": data["comentario"],
                    "created_at": datetime.now()
                }
            )
            row = result.fetchone()
            self.db.commit()
            if row:
                return dict(row._mapping)
            return None

        except CustomException as e:
            print(f"Error al guardar registro de anulación: {e}")
            self.db.rollback()
            raise CustomException("Error al guardar registro de anulación.")
        finally:
            self.db.close()

    # Query para consultar registro de anulación
    def consultar_registro_anulacion(self, oc: int):
        try:
            sql = """
                SELECT * FROM dbo.anulacion_ordenes_compra
                WHERE numero = :oc AND estado = 1
            """
            result = self.db.execute(text(sql), {"oc": oc}).fetchone()
            return dict(result._mapping) if result else None
        except Exception as e:
            print(f"Error al consultar registro de anulación: {e}")
            raise CustomException("Error al consultar registro de anulación.")
        finally:
            self.db.close()

    # Query para consultar registro de anulación
    def consultar_registro_anulacion_x_id(self, id: int):
        try:
            sql = """
                SELECT * FROM dbo.anulacion_ordenes_compra
                WHERE id = :id AND estado = 1
            """
            result = self.db.execute(text(sql), {"id": id}).fetchone()
            return dict(result._mapping) if result else None
        except Exception as e:
            print(f"Error al consultar registro de anulación: {e}")
            raise CustomException("Error al consultar registro de anulación.")
        finally:
            self.db.close()

    # Query para anular cabecera de OC
    def anular_cabecera_oc(self, oc: int):
        try:
            sql = """
                UPDATE dbo.documentos_ped SET anulado = 1
                WHERE numero = :oc AND sw = 3
            """
            self.db.execute(text(sql), {"oc": oc})
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error al anular cabecera de OC: {e}")
            self.db.rollback()
            raise CustomException("Error al anular cabecera de OC.")
        finally:
            self.db.close()

    # Query para eliminar ítems de OC
    def eliminar_items_oc(self, oc: int):
        try:
            sql = """
                DELETE FROM dbo.documentos_lin_ped
                WHERE numero = :oc AND sw = 3
            """
            self.db.execute(text(sql), {"oc": oc})
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar ítems de OC: {e}")
            self.db.rollback()
            raise CustomException("Error al eliminar ítems de OC.")
        finally:
            self.db.close()

    # Query para actualizar registro de anulación
    def actualizar_registro_anulacion(
        self, 
        id: int, 
        numero_oc: int, 
        anulado: int, 
        equipo: str,
        equipo_nombre: str
    ):
        try:
            sql = """
                UPDATE dbo.anulacion_ordenes_compra
                SET anulado = :anulado, equipo = :equipo, equipo_nombre = :equipo_nombre
                WHERE id = :id AND numero = :numero_oc AND estado = 1
            """
            self.db.execute(text(sql), {
                "numero_oc": numero_oc, 
                "id": id, 
                "anulado": anulado, 
                "equipo": equipo,
                "equipo_nombre": equipo_nombre
            })
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar registro de anulación: {e}")
            self.db.rollback()
            raise CustomException("Error al actualizar registro de anulación.")
        finally:
            self.db.close()

    # Query para obtener email por usuario
    def get_mail_by_username(self, usuario: str):
        try:
            sql = """
                SELECT t.mail 
                FROM usuarios u
                INNER JOIN terceros t ON t.nit = u.nit
                WHERE u.usuario = :usuario
            """
            result = self.db.execute(text(sql), {"usuario": usuario}).fetchone()
            return dict(result._mapping)["mail"] if result else None
        except Exception as e:
            print(f"Error al obtener email por usuario: {e}")
            raise CustomException("Error al obtener email por usuario.")
        finally:
            self.db.close()

    # Query para obtener tercero por NIT
    def buscar_tercero(self, nit):
        try:
            sql = """ SELECT * FROM terceros WHERE nit = :nit """
            result = self.db.execute(text(sql), {"nit": nit}).fetchone()
            return dict(result._mapping) if result else None
        except Exception as e:
            print(f"Error al obtener tercero por NIT: {e}")
            raise CustomException("Error al obtener tercero por NIT.")
        finally:
            self.db.close()

    # Query para obtener condición de pago
    def obtener_condicion_pago(self, condicion):
        try:
            sql = """ SELECT descripcion FROM condiciones_pago WHERE condicion = :condicion """
            result = self.db.execute(text(sql), {"condicion": condicion}).fetchone()
            if not result:
                raise CustomException("Condición de pago no encontrada.")
            return dict(result._mapping)["descripcion"]
        except CustomException as e:
            print(f"Error al obtener condición de pago: {e}")
            raise CustomException(f"{e}")
        finally:
            self.db.close()

    # def obtener_detalles_oc(self, orden: str):
    #     sql = """
    #     SELECT numero, codigo, seq, adicional, cantidad, valor_unitario, porcentaje_descuento, und,
    #         vlr_unit = CASE 
    #             WHEN porcentaje_descuento <> 0 THEN valor_unitario * ((100 - porcentaje_descuento) / 100)
    #             ELSE valor_unitario
    #         END,
    #         total = cantidad * (
    #             CASE 
    #                 WHEN porcentaje_descuento <> 0 THEN valor_unitario * ((100 - porcentaje_descuento) / 100)
    #                 ELSE valor_unitario
    #             END
    #         ),
    #         adic = isnull(adicional, 1)
    #     FROM documentos_lin_ped_historia
    #     WHERE sw = 3 AND numero = :orden
    #     """
    #     result = self.db.execute(text(sql), {"orden": orden}).fetchall()
        
    #     # Mapear filas a dict
    #     return [dict(row._mapping) for row in result] if result else []

    def _parse_pedido_from_adic(self, adic: str) -> Tuple[str, str, bool]:
        """
        Devuelve (pedido, nota, es_stock)
        - STOCK*  => ("--", "", True)
        - len=5   => (adic, "", False)
        - len>5   => (adic[:5], adic, False)
        - otros   => ("", "", False)
        """
        if not adic:
            return ("", "", False)
        adic = adic.strip()
        if adic.upper().startswith("STOCK"):
            return ("--", "", True)
        if len(adic) == 5:
            return (adic, "", False)
        if len(adic) > 5:
            return (adic[:5], adic, False)
        return ("", "", False)

    def _round2(self, x):
        return None if x is None else round(float(x), 2)

    def build_oc_detalle(self, orden: str, moneda: str, dolar3: float, euro3: float) -> Dict[str, Any]:
        """
        Retorna:
        {
        'orden': str,
        'conf': 0|1,
        'items': [ { ...campos calculados... } ],
        'totales': { 'costotal': float, 'totalprecio': float, 'utilidadtotal': float }
        }
        """
        # 1) Traer items de la OC (historia)
        rows = self.db.execute(text("""
            SELECT
                numero,
                codigo,
                seq,
                adicional,
                cantidad,
                valor_unitario,
                porcentaje_descuento,
                und,
                cantidad * valor_unitario * ((100 - porcentaje_descuento)/100.0) AS total,
                ISNULL(adicional, 1) AS adic
            FROM documentos_lin_ped_historia
            WHERE sw = 3 AND numero = :orden
        """), {"orden": orden}).fetchall()

        if not rows:
            return {"orden": orden, "conf": 0, "items": [], "totales": {"costotal": 0.0, "totalprecio": 0.0, "utilidadtotal": 0.0}}

        items_base = [dict(r._mapping) for r in rows]

        # Conjuntos para batch queries
        codigos: Set[str] = set()
        pedidos_necesarios: Set[str] = set()

        # Pre-proceso adic y vlr_unit
        for it in items_base:
            it["porcentaje_descuento"] = it.get("porcentaje_descuento") or 0
            it["vlr_unit"] = it["valor_unitario"] * ((100 - it["porcentaje_descuento"]) / 100.0) if it["porcentaje_descuento"] else it["valor_unitario"]

            pedido, nota, es_stock = self._parse_pedido_from_adic(str(it.get("adic", "") or ""))
            it["pedido"] = pedido
            it["nota"] = nota
            it["es_stock"] = es_stock

            codigos.add(it["codigo"])
            if pedido and pedido != "--":
                pedidos_necesarios.add(pedido)

        # 2) STOCK por código (excluye bodegas)
        stock_map = {}
        print(f"codigos: {codigos}")
        if codigos:
            stock_rows = self.db.execute(text(f"""
                SELECT codigo, SUM(stock) AS stockk
                FROM v_referencias_sto_hoy
                WHERE bodega NOT IN (3,4,7,8,9,19,20,21,22)
                AND codigo IN :codigos
                AND ano = YEAR(GETDATE())
                AND mes = MONTH(GETDATE())
                GROUP BY codigo
            """), {"codigos": tuple(codigos)}).fetchall()
            for r in stock_rows:
                v = int(r.stockk or 0)
                stock_map[r.codigo] = max(v, 0)

        # 3) Pedidos pendientes (sw=1) por código
        pedidoc_map = {}
        ped_rows = self.db.execute(text(f"""
            SELECT l.codigo, SUM(l.cantidad - l.cantidad_despachada) AS debe
            FROM documentos_lin_ped l
            JOIN documentos_ped d
            ON l.sw = d.sw AND l.numero = d.numero AND l.bodega = d.bodega
            WHERE d.sw = 1 AND l.codigo IN :codigos
            GROUP BY l.codigo
        """), {"codigos": tuple(codigos)}).fetchall()
        for r in ped_rows:
            pedidoc_map[r.codigo] = int(r.debe or 0)

        # 4) Otras OCs (sw=3) por código (excluye esta numero)
        otraoc_map = {}
        oc_rows = self.db.execute(text(f"""
            SELECT codigo, SUM(cantidad - cantidad_despachada) AS otraoc
            FROM documentos_lin_ped
            WHERE sw = 3 AND numero <> :orden AND codigo IN :codigos
            GROUP BY codigo
        """), {"orden": orden, "codigos": tuple(codigos)}).fetchall()
        for r in oc_rows:
            v = int(r.otraoc or 0)
            otraoc_map[r.codigo] = max(v, 0)

        # 5) Costos (preferir FOB; si no, costo_base)
        costo_fob = {}
        if codigos:
            for r in self.db.execute(text("SELECT codigo, costo_unitario_fob FROM referencias_imp WHERE codigo IN :codigos"),
                                {"codigos": tuple(codigos)}):
                if r.costo_unitario_fob is not None:
                    costo_fob[r.codigo] = float(r.costo_unitario_fob)

        costo_base = {}
        if codigos:
            for r in self.db.execute(text("SELECT codigo, costo_base FROM ref_gen_costo WHERE codigo IN :codigos"),
                                {"codigos": tuple(codigos)}):
                if r.costo_base is not None:
                    costo_base[r.codigo] = float(r.costo_base)

        # 6) Referencias (descripcion + clase) y Clase→descripcion (marca)
        ref_map = {}
        if codigos:
            for r in self.db.execute(text("SELECT codigo, descripcion, clase, und_vta FROM referencias WHERE codigo IN :codigos"),
                                {"codigos": tuple(codigos)}):
                ref_map[r.codigo] = {"descripcion": r.descripcion, "clase": r.clase, "und_vta": r.und_vta}

        clases: Set[str] = set([v["clase"] for v in ref_map.values() if v.get("clase")])
        clase_desc = {}
        if clases:
            for r in self.db.execute(text("SELECT clase, descripcion FROM referencias_cla WHERE clase IN :clases"),
                                {"clases": tuple(clases)}):
                clase_desc[r.clase] = r.descripcion

        # 7) Datos por pedido (si hay)
        # 7.1 documentos_ped_historia (sw=1) para moneda y nit
        ped_info = {}       # numero -> {moneda, nit}
        nits: Set[str] = set()
        if pedidos_necesarios:
            for r in self.db.execute(text("""
                SELECT numero, moneda, nit
                FROM documentos_ped_historia
                WHERE sw = 1 AND numero IN :peds
            """), {"peds": tuple(pedidos_necesarios)}):
                ped_info[r.numero] = {"moneda": r.moneda, "nit": r.nit}
                if r.nit: nits.add(r.nit)

        # 7.2 documentos_lin_ped (sw=1) para valor_unitario/adicional/cantidad por (numero,codigo)
        ped_line_map = {}   # (numero,codigo) -> {valor_unitario, adicional, cantidad}
        if pedidos_necesarios:
            for r in self.db.execute(text("""
                SELECT numero, codigo, valor_unitario, adicional, cantidad
                FROM documentos_lin_ped
                WHERE sw = 1 AND numero IN :peds AND codigo IN :codigos
            """), {"peds": tuple(pedidos_necesarios), "codigos": tuple(codigos)}):
                ped_line_map[(r.numero, r.codigo)] = {
                    "valor_unitario": float(r.valor_unitario or 0),
                    "adicional": r.adicional,
                    "cantidad": float(r.cantidad or 0),
                }

        # 7.3 terceros → nombre y ciudad/dpto
        ter_map = {}        # nit -> {nombres, y_ciudad, y_dpto}
        if nits:
            for r in self.db.execute(text("""
                SELECT nit, nombres, y_ciudad, y_dpto
                FROM terceros
                WHERE nit IN :nits
            """), {"nits": tuple(nits)}):
                ter_map[r.nit] = {"nombres": r.nombres, "y_ciudad": r.y_ciudad, "y_dpto": r.y_dpto}

        # 7.4 y_ciudades → descripción (ciudad)
        ciudad_desc_map = {}  # (ciudad,dpto) -> descripcion
        ciudad_keys = set()
        for nit, t in ter_map.items():
            if t.get("y_ciudad") and t.get("y_dpto"):
                ciudad_keys.add((t["y_ciudad"], t["y_dpto"]))
        if ciudad_keys:
            # arma parámetros IN para tupla compuesta con OR
            # más simple: traer todas y filtrar en Python (si el dataset no es enorme)
            for (ciudad, dpto) in ciudad_keys:
                r = self.db.execute(text("""
                    SELECT descripcion
                    FROM y_ciudades
                    WHERE ciudad = :ciudad AND departamento = :dpto
                """), {"ciudad": ciudad, "dpto": dpto}).fetchone()
                if r:
                    ciudad_desc_map[(ciudad, dpto)] = r.descripcion

        # 8) Construir respuesta por ítem
        conf = 0
        costotal = 0.0
        totalprecio = 0.0
        out_items: List[Dict[str, Any]] = []

        for it in items_base:
            codigo = it["codigo"]
            cantidad = float(it["cantidad"] or 0)
            vlr_unit = float(it["vlr_unit"] or 0)
            und = it.get("und")

            # stock/pedido/otra oc
            stockp = int(stock_map.get(codigo, 0))
            pedidoc = int(pedidoc_map.get(codigo, 0))
            totaloc = int(otraoc_map.get(codigo, 0))

            # referencia + marca
            refd = ref_map.get(codigo, {})
            ref_descripcion = refd.get("descripcion")
            marca = clase_desc.get(refd.get("clase"))

            # costo preferencia: FOB -> base
            if codigo in costo_fob:
                costo = float(costo_fob[codigo])
            else:
                costo = float(costo_base.get(codigo, 0))

            # Datos de pedido (si no es STOCK)
            monedap = None
            valor_item = 0.0
            fecha_entrega = "&nbsp;"
            cliente = None
            ciudad = None

            if it["pedido"] and it["pedido"] != "--":
                pednum = it["pedido"]

                # moneda/nit del pedido
                pinfo = ped_info.get(pednum, {})
                monedap = pinfo.get("moneda")
                nit = pinfo.get("nit")

                # línea del pedido para este código
                pl = ped_line_map.get((pednum, codigo))
                if pl:
                    valor_item = float(pl["valor_unitario"] or 0)
                    # Si monedap=2 en ASP multiplicaban por dolar3 (aquí haremos igual)
                    if monedap == 2:
                        valor_item = valor_item * float(dolar3)
                    fecha_entrega = pl.get("adicional") or "&nbsp;"

                # cliente/ciudad
                if nit and nit in ter_map:
                    t = ter_map[nit]
                    cliente = t.get("nombres")
                    key = (t.get("y_ciudad"), t.get("y_dpto"))
                    ciudad = ciudad_desc_map.get(key)

            # Utilidades por ítem
            utilidad = 0.0
            utilidadt = 0.0
            if valor_item:
                if moneda in ("2", "6"):
                    utilidad = ((valor_item - (vlr_unit * float(dolar3))) / valor_item) * 100
                    utilidadt = (((valor_item * cantidad) - ((vlr_unit * cantidad) * float(dolar3))) / (valor_item * cantidad)) * 100
                elif moneda == "3":
                    utilidad = ((valor_item - (vlr_unit * float(euro3))) / valor_item) * 100
                else:  # "1" o None
                    utilidad = ((valor_item - vlr_unit) / valor_item) * 100
                    utilidadt = (((valor_item * cantidad) - (vlr_unit * cantidad)) / (valor_item * cantidad)) * 100

            # Conflicto si redondeos difieren
            if round(utilidad or 0, 0) != round(utilidadt or 0, 0):
                conf = 1

            # Ajuste de valor_item si monedap=2 (en ASP dividían al imprimir unitario)
            if monedap == 2 and valor_item:
                valor_item = valor_item / float(dolar3)

            # Costo total por ítem (según moneda)
            if moneda == "2":
                costotal += float(it["total"] or 0) * float(dolar3)
                costo_total_item = float(it["total"] or 0) * float(dolar3)
            elif moneda == "3":
                costotal += float(it["total"] or 0) * float(euro3)
                costo_total_item = float(it["total"] or 0) * float(euro3)
            else:
                costotal += float(it["total"] or 0)
                costo_total_item = float(it["total"] or 0)

            # Precio total por ítem
            precioxitem = (valor_item or 0) * cantidad
            totalprecio += precioxitem

            # bandera cantidad en rojo si no cuadra:
            cantidad_en_conflicto = int(pedidoc) != (int(cantidad) + (int(stockp) + int(totaloc)))
            if cantidad_en_conflicto:
                conf = 1

            out_items.append({
                "numero": it["numero"],
                "codigo": codigo,
                "seq": it["seq"],
                "nota": it["nota"],
                "cantidad": int(cantidad),
                "pedidoc": int(pedidoc),
                "stock": int(stockp),
                "otras_oc": int(totaloc),
                "descripcion": ref_descripcion,
                "marca": marca,
                "und": und,
                "costo": self._round2(costo),
                "vlr_unit": self._round2(vlr_unit),
                "valor_item": self._round2(valor_item),
                "utilidad": round(utilidad or 0, 0),
                "cliente": cliente or ("STOCK AVANTIKA" if it["es_stock"] else None),
                "ciudad": ciudad or ("BARRANQUILLA" if it["es_stock"] else None),
                "fecha_entrega": fecha_entrega,
                "costo_total_item": self._round2(costo_total_item),
                "precio_total_item": self._round2(precioxitem),
                "cantidad_conflictiva": cantidad_en_conflicto
            })

        # 9) Utilidad total
        utilidadtotal = 0.0
        if totalprecio:
            if (monedap == 2):  # si el último monedap importa; en el ASP usan monedap que viene de un pedido
                utilidadtotal = (((totalprecio * float(dolar3)) - costotal) / (totalprecio * float(dolar3))) * 100
            elif (monedap == 3):
                utilidadtotal = (((totalprecio * float(euro3)) - costotal) / (totalprecio * float(euro3))) * 100
            else:
                utilidadtotal = ((totalprecio - costotal) / totalprecio) * 100

        return {
            "orden": orden,
            "conf": conf,
            "items": out_items,
            "totales": {
                "costotal": self._round2(costotal),
                "totalprecio": self._round2(totalprecio),
                "utilidadtotal": round(utilidadtotal or 0, 0)
            }
        }
