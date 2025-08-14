from Utils.tools import Tools, CustomException
from sqlalchemy import text

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
