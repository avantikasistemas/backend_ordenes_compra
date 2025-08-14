from Utils.tools import Tools, CustomException
from Utils.querys import Querys
from datetime import datetime
from fastapi import Response
import pandas as pd
from io import BytesIO

class Seguimiento:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()
        self.querys = Querys(self.db)

    # Función que se encarga de guardar los registros
    def guardar_seguimiento(self, data: dict):

        try:
            self.querys.guardar_seguimiento(data)
            
            # Retornamos la información.
            return self.tools.output(200, "Seguimiento guardado con exito.")

        except Exception as e:
            print(f"Error al obtener información de seguimiento: {e}")
            raise CustomException("Error al obtener información de seguimiento.")

    # Función que se encarga de cargar los datos de seguimiento
    def cargar_datos_seguimiento(self, data: dict):

        try:
            oc = data["oc"]

            seguimientos = self.querys.cargar_datos_seguimiento(oc)

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", seguimientos)

        except Exception as e:
            print(f"Error al obtener información de seguimiento: {e}")
            raise CustomException("Error al obtener información de seguimiento.")
