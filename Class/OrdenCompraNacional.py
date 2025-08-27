from Utils.tools import Tools, CustomException
from Utils.querys import Querys
from datetime import datetime
from fastapi import Response
import pandas as pd
from io import BytesIO

class OrdenCompraNacional:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()
        self.querys = Querys(self.db)

    # Función para obtener las ordenes de compra, según filtros
    def buscar_oc_nacional(self, data: dict):
        """ Api que realiza la consulta de la orden de compra. """

        # Asignamos nuestros datos de entrada a sus respectivas variables
        oc = data["oc"]
        tasa = data["tasa"]
        factor = data["factor"]
        tasav = 1
        euro3 = tasa * factor
        euro4 = tasa * factor

        try:
            # Buscamos la orden de compra
            datos_oc = self.querys.buscar_oc_nacional(oc, tasa, factor)
            if not datos_oc:
                raise CustomException(
                    "No se encontró información para la orden de compra.")
            
            moneda = datos_oc.get("moneda", "")
            if moneda != "PESOS":
                tasav = tasa

            data_tercero = self.querys.buscar_tercero(datos_oc["nit"])
            if not data_tercero:
                raise CustomException("No se encontró información del tercero.")
            
            condicion_tercero = self.querys.obtener_condicion_pago(
                data_tercero["condicion"]
            )
            condicion_orden = self.querys.obtener_condicion_pago(
                datos_oc["condicion"]
            )
            
            datos = self.querys.build_oc_detalle(oc, moneda, tasav, euro3)
            
            # detalles = self.querys.obtener_detalles_oc(oc)

            # datos_oc["condicion_tercero"] = condicion_tercero
            # datos_oc["condicion_orden"] = condicion_orden
            # datos_oc["fecha_formateada"] = self.tools.format_date(
            #     str(datos_oc["fecha"]), "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"
            # )
            # datos_oc["tasav"] = f"${tasav:,.0f}".replace(",", ".")
            # datos_oc["data_tercero"] = data_tercero
            # datos_oc["items"] = detalles

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", datos_oc)

        except CustomException as e:
            print(f"Error al obtener información de orden de compra: {e}")
            raise CustomException(f"{e}")
