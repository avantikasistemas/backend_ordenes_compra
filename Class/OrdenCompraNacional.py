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
        
        print(data)

        try:
            if oc:
                oc = oc.strip()

            datos_oc = self.querys.buscar_oc_nacional(oc, tasa, factor)

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", datos_oc)

        except Exception as e:
            print(f"Error al obtener información de orden de compra: {e}")
            raise CustomException("Error al obtener información de orden de compra.")
