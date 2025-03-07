from Utils.tools import Tools, CustomException
from Utils.querys import Querys
from datetime import datetime
from fastapi import Response
import pandas as pd
from io import BytesIO

class OrdenCompra:

    def __init__(self):
        self.tools = Tools()
        self.querys = Querys()

    def get_orden_compra_data(self, data: dict):
        """ Api que realiza la consulta del tercero a la base de datos. """

        # Asignamos nuestros datos de entrada a sus respectivas variables
        oc = data["oc"]

        try:
            if oc:
                data["oc"] = oc.strip()

            datos_oc = self.querys.consultar_orden_compra(data)

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", datos_oc)

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

            datos_oc = self.querys.consultar_orden_compra(data)

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

        try:

            self.querys.guardar_registro_estado_oc(data)
            
            # Retornamos la información.
            return self.tools.output(200, "Registro guardado con exito.", data)

        except Exception as e:
            print(f"Error al obtener información de orden de compra: {e}")
            raise CustomException("Error al obtener información de orden de compra.")
