from .validator import Validator


class Rules:
    """ Esta clase se encarga de validar los datos de entrada de la API
        y si hay un error, lanza una excepcion """

    val = Validator()

    def __init__(self, path: str, params: dict):
        path_dict = {
            "/get_orden_compra_data": self.__val_get_orden_compra_data,
        }
        # Se obtiene la funcion a ejecutar
        func = path_dict.get(path, None)
        if func:
            # Se ejecuta la funcion para obtener las reglas de validacion
            validacion_dict = func(params)

            # Se valida la datas
            self.val.validacion_datos_entrada(validacion_dict)

    def __val_get_orden_compra_data(self, params):
        validacion_dict = [
            {
                "tipo": "string",
                "campo": "orden de compra",
                "valor": params["oc"],
                "obligatorio": False,
            },
            {
                "tipo": "string",
                "campo": "fecha orden de compra desde ",
                "valor": params["fecha_oc_desde"],
                "obligatorio": False,
            },
            {
                "tipo": "string",
                "campo": "fecha orden de compra hasta",
                "valor": params["fecha_oc_hasta"],
                "obligatorio": False,
            },
            {
                "tipo": "string",
                "campo": "solicitud de aprobación",
                "valor": params["solicitud_aprobacion"],
                "obligatorio": False,
            },
            {
                "tipo": "string",
                "campo": "usuario",
                "valor": params["usuario"],
                "obligatorio": False,
            },
            {
                "tipo": "string",
                "campo": "enviada proveedor",
                "valor": params["enviada_proveedor"],
                "obligatorio": False,
            },
            {
                "tipo": "string",
                "campo": "confirmada proveedor",
                "valor": params["confirmada_proveedor"],
                "obligatorio": False,
            }
        ]
        return validacion_dict
