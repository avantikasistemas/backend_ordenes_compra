from Utils.tools import Tools, CustomException
from Utils.querys import Querys
from datetime import datetime
from fastapi import Response
import pandas as pd
from io import BytesIO

class OrdenCompra:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()
        self.querys = Querys(self.db)

    def get_orden_compra_data(self, data: dict):
        """ Api que realiza la consulta del tercero a la base de datos. """

        # Asignamos nuestros datos de entrada a sus respectivas variables
        oc = data["oc"]

        try:
            if oc:
                data["oc"] = oc.strip()

            if data["position"] <= 0:
                message = "El campo posición no es válido"
                raise CustomException(message)

            datos_oc = self.querys.consultar_orden_compra(data)

            registros = datos_oc["registros"]
            cant_registros = datos_oc["cant_registros"]

            if not registros:
                message = "No hay listado de reportes que mostrar."
                return self.tools.output(200, message, data={
                "total_registros": 0,
                "total_pag": 0,
                "posicion_pag": 0,
                "registros": []
            })

            if cant_registros%data["limit"] == 0:
                total_pag = cant_registros//data["limit"]
            else:
                total_pag = cant_registros//data["limit"] + 1

            if total_pag < int(data["position"]):
                message = "La posición excede el número total de registros."
                return self.tools.output(200, message, data={
                "total_registros": 0,
                "total_pag": 0,
                "posicion_pag": 0,
                "registros": []
            })

            registros_dict = {
                "total_registros": cant_registros,
                "total_pag": total_pag,
                "posicion_pag": data["position"],
                "registros": registros
            }

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", registros_dict)

        except Exception as e:
            print(f"Error al obtener información de orden de compra: {e}")
            raise CustomException("Error al obtener información de orden de compra.")

    def generar_excel(self, data: dict):
        """ Api que realiza la consulta del tercero a la base de datos. """

        # Asignamos nuestros datos de entrada a sus respectivas variables
        oc = data["oc"]

        try:
            if oc:
                data["oc"] = oc.strip()

            datos_oc = self.querys.consultar_orden_compra_excel(data)

            datos_excel = self.exportar_excel(datos_oc)

            return Response(
                content=datos_excel["output"].read(), 
                headers=datos_excel["headers"], 
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            print(f"Error al obtener información de orden de compra: {e}")
            raise CustomException("Error al obtener información de orden de compra.")

    def exportar_excel(self, datos: list):

        # Convertir los datos a un DataFrame de pandas
        df = pd.DataFrame(datos)

        # Eliminar la columna que no queremos exportar (por ejemplo, "oculto")
        df = df.drop(columns=["consecutivo"])
        df = df.drop(columns=["enviada_a_aprobar"])
        df = df.drop(columns=["enviada_a_proveedor"])
        df = df.drop(columns=["confirmada_por_proveedor"])

        # Crear un buffer de memoria para el archivo Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Datos")

        # Obtener los bytes del archivo y preparar la respuesta
        output.seek(0)
        headers = {
            "Content-Disposition": "attachment; filename=datos.xlsx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        return {"output": output, "headers": headers}

    def guardar_registro_estado_oc(self, data: dict):
        """ Api que realiza la consulta del tercero a la base de datos. """

        ordenes = data["ordenes"]

        try:
            if ordenes:
                for orden in ordenes:
                    aprobada = None
                    if orden["autorizada"] == "SI":
                        aprobada = 1
                    elif orden["autorizada"] == "NO":
                        aprobada = 0
                    data_insert = {
                        "oc": orden["numero"],
                        "aprobada": aprobada,
                        "enviada_a_aprobar": orden["enviada_a_aprobar"],
                        "enviada_al_proveedor": orden["enviada_a_proveedor"],
                        "confirmada_por_proveedor": orden["confirmada_por_proveedor"],
                        "fecha_envio_al_proveedor": orden["fecha_envio_proveedor"],
                        "observaciones": orden["observaciones"],
                    }
                    self.querys.guardar_registro_estado_oc(data_insert)
            
            # Retornamos la información.
            return self.tools.output(200, "Registro guardado con exito.", data)

        except Exception as e:
            print(f"Error al obtener información de orden de compra: {e}")
            raise CustomException("Error al obtener información de orden de compra.")
