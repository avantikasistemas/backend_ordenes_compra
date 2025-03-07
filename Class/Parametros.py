from Utils.tools import Tools, CustomException
from Utils.querys import Querys

class Parametros:

    def __init__(self):
        self.tools = Tools()
        self.querys = Querys()

    def get_usuarios(self):
        """ Api que realiza la consulta de los estados. """

        try:
            # Acá usamos la query para traer la información
            datos = self.querys.get_usuarios()

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", datos)

        except Exception as e:
            print(f"Error al obtener información de tercero: {e}")
            raise CustomException("Error al obtener información de tercero.")
