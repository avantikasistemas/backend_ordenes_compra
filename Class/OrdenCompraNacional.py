import socket
from Utils.tools import Tools, CustomException
from Utils.querys import Querys
from datetime import datetime
from fastapi import Response
import pandas as pd
from io import BytesIO
import os

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
            nombre_moneda = datos_oc.get("nombre_moneda", "")
            
            # Si no es PESOS, la tasa es la que ingresó el usuario
            if nombre_moneda != "PESOS":
                tasav = tasa

            # Obtener datos del tercero (proveedor)
            data_tercero = self.querys.buscar_tercero(datos_oc["nit"])
            if not data_tercero:
                raise CustomException("No se encontró información del tercero.")
            
            # Obtener condiciones de pago
            condicion_tercero = self.querys.obtener_condicion_pago(
                data_tercero["condicion"]
            )
            condicion_orden = self.querys.obtener_condicion_pago(
                datos_oc["condicion"]
            )
            
            # Obtener el detalle completo de la OC con todos los cálculos
            datos_detalle = self.querys.build_oc_detalle(oc, moneda, tasav, euro3)
            
            # Obtener usuario que creó la OC
            usuario_oc = self.querys.obtener_usuario_oc(oc)
            
            # Obtener historial de autorizaciones
            autorizaciones = self.querys.obtener_historial_autorizaciones(oc)
            
            # Formatear fecha
            fecha_formateada = self.tools.format_date(
                str(datos_oc["fecha"]), "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"
            )
            
            # Formatear tasa con separadores de miles
            tasav_formateado = f"${tasav:,.2f}".replace(",", ".")

            # Construir respuesta completa
            respuesta = {
                "oc": oc,
                "fecha": datos_oc["fecha"],
                "fecha_formateada": fecha_formateada,
                "moneda": moneda,
                "nombre_moneda": nombre_moneda,
                "tasav": tasav,
                "tasav_formateado": tasav_formateado,
                "tasa": tasa,
                "factor": factor,
                "euro3": euro3,
                "euro4": euro4,
                "nit": datos_oc["nit"],
                "condicion_tercero": condicion_tercero,
                "condicion_orden": condicion_orden,
                "data_tercero": data_tercero,
                "usuario_oc": usuario_oc,
                "conf": datos_detalle["conf"],  # Indicador de conflictos
                "items": datos_detalle["items"],
                "totales": datos_detalle["totales"],
                "autorizaciones": autorizaciones
            }

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", respuesta)

        except CustomException as e:
            print(f"Error al obtener información de orden de compra: {e}")
            raise CustomException(f"{e}")

    def solicitar_autorizacion(self, data: dict):
        """ Envía correo de solicitud de autorización para una OC """
        
        oc = data["oc"]
        dolar = data["dolar"]
        euro = data["euro"]
        usuario = data["usuario"]
        comentario = data.get("comentario", "")
        
        try:
            # Construir URL del cuerpo del correo
            # En el ASP original apuntaba a: list_oc_send_kit.asp
            # Obtener URL base del frontend
            frontend_url = os.getenv("FRONTEND_BASE_URL", "http://130.1.64.103:5174")
            cuerpo_url = f"{frontend_url}/list_oc_send_kit.asp?oc={oc}&dolare={dolar}&euroe={euro}&notas={comentario}"
            
            # Determinar remitente según usuario
            email_map = {
                "MMIRANDA2": "auxiliartic@avantika.com.co",
                # "MMIRANDA2": "negociador3@avantika.com.co",
                # "MCASALINS": "negociador1@avantika.com.co",
                # "KMERCADO": "negociador4@avantika.com.co",
                # "PCARBONELL": "compras@avantika.com.co",
                # "CONTADOR": "sistemas@avantika.com.co"
            }
            
            de = email_map.get(usuario, "compras@avantika.com.co")
            
            # Determinar destinatarios según usuario
            if usuario == "CONTADOR":
                # para = ["gerencia@avantika.com.co", "contador@avantika.com.co"]
                para = ["sistemas@avantika.com.co"]
            else:
                para = [
                    "sistemas@avantika.com.co",
                    # "gerencia@avantika.com.co",
                    # "compras@avantika.com.co",
                    # "negociador4@avantika.com.co"
                ]
            
            # BCC (copia oculta)
            bcc = [
                # "tic@avantika.com.co",
                # "negociador3@avantika.com.co",
                # "negociador4@avantika.com.co",
                # "negociador1@avantika.com.co",
                # "sistemas@avantika.com.co"
                "auxiliartic@avantika.com.co"
            ]
            
            # Obtener datos básicos para el encabezado del correo
            datos_oc = self.querys.buscar_oc_nacional(oc, 0, 0)
            moneda = datos_oc.get("moneda", "1")
            
            # Obtener tercero y condiciones
            data_tercero = self.querys.buscar_tercero(datos_oc["nit"])
            condicion_tercero = self.querys.obtener_condicion_pago(data_tercero["condicion"])
            condicion_orden = self.querys.obtener_condicion_pago(datos_oc["condicion"])
            
            # Formateos iniciales
            fecha_formateada = self.tools.format_date(str(datos_oc["fecha"]), "%Y-%m-%d %H:%M:%S", "%d/%m/%Y")
            nombre_moneda = datos_oc.get("nombre_moneda", "")
            
            # Obtener el detalle calculado
            detalles = self.querys.build_oc_detalle(oc, moneda, dolar, euro)
            items = detalles.get("items", [])
            totales = detalles.get("totales", {})

            # --- CONSTRUCCIÓN DEL HTML COMPLETO TIPO VISTA FRONTEND ---
            
            # Estilos CSS inline para asegurar compatibilidad en correos
            style_table = "width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 10px; border: 1px solid #ccc;"
            style_th = "background-color: #f4f6f8; color: #333; font-weight: bold; padding: 5px; border: 1px solid #ccc; text-align: center;"
            style_td = "padding: 5px; border: 1px solid #ccc; color: #333;"
            style_right = "text-align: right;"
            style_center = "text-align: center;"
            style_header_box = "background-color: #f9fafb; padding: 10px; border: 1px solid #e5e7eb; margin-bottom: 15px; font-family: Arial, sans-serif; font-size: 12px; color: #374151;"
            style_total_row = "background-color: #f4f6f8; font-weight: bold;"
            style_utilidad_row = "background-color: #e0e7ff; font-weight: bold; color: #2c5282; font-size: 14px;"

            # 1. Encabezado Informativo
            info_html = f"""
            <div style="{style_header_box}">
                <div style="margin-bottom: 5px;">
                    <strong>Fecha:</strong> {fecha_formateada} - <strong>OC{oc}</strong> &nbsp;&nbsp; 
                    <strong>Moneda OC:</strong> {nombre_moneda}
                </div>
                <div style="margin-bottom: 5px;">
                    <strong>Proveedor:</strong> {data_tercero.get('nombres', '')} - {data_tercero.get('y_ciudad', '')} &nbsp;&nbsp; 
                    <strong>Teléfono:</strong> {data_tercero.get('telefono_1', '')}
                </div>
                <div style="margin-bottom: 5px;">
                    <strong>Condición de Pago Proveedor:</strong> {condicion_tercero}
                </div>
                <div>
                    <strong>Condición de pago de esta orden de compra:</strong> {condicion_orden}
                </div>
            </div>
            """

            # 2. Tabla de Items
            tabla_html = f"""
            {info_html}
            <table style="{style_table}">
                <thead>
                    <tr>
                        <th rowspan="2" style="{style_th}">Item</th>
                        <th rowspan="2" style="{style_th}">Código</th>
                        <th rowspan="2" style="{style_th}">Obs.</th>
                        <th rowspan="2" style="{style_th}">Cant.<br>Comprar</th>
                        <th rowspan="2" style="{style_th}">Cant.<br>Pedida</th>
                        <th rowspan="2" style="{style_th}">Stock</th>
                        <th rowspan="2" style="{style_th}">Backorder</th>
                        <th rowspan="2" style="{style_th}">Descripción</th>
                        <th rowspan="2" style="{style_th}">Marca</th>
                        <th rowspan="2" style="{style_th}">Pres.</th>
                        <th colspan="3" style="{style_th}">Valores antes de IVA</th>
                        <th rowspan="2" style="{style_th}">% Util.</th>
                        <th rowspan="2" style="{style_th}">KIT</th>
                        <th rowspan="2" style="{style_th}">Cliente</th>
                        <th rowspan="2" style="{style_th}">Ciudad</th>
                        <th rowspan="2" style="{style_th}">Fecha<br>Compromiso</th>
                        <th rowspan="2" style="{style_th}">Costo Total<br>Item</th>
                        <th rowspan="2" style="{style_th}">Precio Total<br>Item</th>
                    </tr>
                    <tr>
                        <th style="{style_th}">Costo<br>Cotizado</th>
                        <th style="{style_th}">Costo Unit.<br>Comprar</th>
                        <th style="{style_th}">Precio Venta<br>Unitario</th>
                    </tr>
                </thead>
                <tbody>
            """

            for index, item in enumerate(items):
                # Formateos
                costo = f"${float(item.get('costo', 0)):,.2f}"
                vlr_unit = f"${float(item.get('vlr_unit', 0)):,.2f}" # Unitario comprar
                p_venta = f"${float(item.get('valor_item', 0)):,.2f}" # Venta unitario
                c_total = f"${float(item.get('costo_total_item', 0)):,.2f}"
                p_total = f"${float(item.get('precio_total_item', 0)):,.2f}"
                
                # Alerta cantidad (Uso de bgcolor para compatibilidad con correos antiguos)
                bg_color_attr = ""
                style_cant = style_center
                if item.get('cantidad_conflictiva'):
                    bg_color_attr = 'bgcolor="#FF0000"'
                    style_cant += " background-color: #ff0000; color: white !important; font-weight: bold;"

                # Link KIT (Simulado)
                link_kit = f"{frontend_url}/consultar-kit?oc={oc}&codigo={item.get('codigo')}&dolar={dolar}&euro={euro}"

                tabla_html += f"""
                    <tr>
                        <td style="{style_td} {style_center}">{index + 1}</td>
                        <td style="{style_td}">{item.get('codigo')}</td>
                        <td style="{style_td}">{item.get('nota') or ''}</td>
                        <td {bg_color_attr} style="{style_td} {style_cant}">{int(item.get('cantidad', 0))}</td>
                        <td style="{style_td} {style_center}">{item.get('pedidoc')}</td>
                        <td style="{style_td} {style_center}">{item.get('stock')}</td>
                        <td style="{style_td} {style_center}">{item.get('otras_oc')}</td>
                        <td style="{style_td}">{item.get('descripcion')}</td>
                        <td style="{style_td}">{item.get('marca') or ''}</td>
                        <td style="{style_td} {style_center}">{item.get('und') or ''}</td>
                        
                        <td style="{style_td} {style_right}">{costo}</td>
                        <td style="{style_td} {style_right}">{vlr_unit}</td>
                        <td style="{style_td} {style_right}">{p_venta}</td>
                        
                        <td style="{style_td} {style_right}">{item.get('utilidad')}%</td>
                        <td style="{style_td} {style_center}">
                            <a href="{link_kit}" style="text-decoration: none; color: blue;">
                                🔍 Revisar
                            </a>
                        </td>
                        <td style="{style_td}">{item.get('cliente') or ''}</td>
                        <td style="{style_td}">{item.get('ciudad') or ''}</td>
                        <td style="{style_td} {style_center}">{item.get('fecha_entrega') or ''}</td>
                        <td style="{style_td} {style_right}">{c_total}</td>
                        <td style="{style_td} {style_right}">{p_total}</td>
                    </tr>
                """

            # Totales (Ajustado colspan a 18 por la columna nueva)
            tot_costo = f"${float(totales.get('costotal', 0)):,.2f}"
            tot_precio = f"${float(totales.get('totalprecio', 0)):,.2f}"
            tot_util = f"{totales.get('utilidadtotal', 0)}%"

            tabla_html += f"""
                    <tr style="{style_total_row}">
                        <td colspan="18" style="{style_td} {style_right}">Total Costo:</td>
                        <td colspan="2" style="{style_td} {style_right}">{tot_costo}</td>
                    </tr>
                    <tr style="{style_total_row}">
                        <td colspan="18" style="{style_td} {style_right}">Total Precio:</td>
                        <td colspan="2" style="{style_td} {style_right}">{tot_precio}</td>
                    </tr>
                    <tr style="{style_utilidad_row}">
                        <td colspan="18" style="{style_td} {style_right} border: none;">Utilidad Total:</td>
                        <td colspan="2" style="{style_td} {style_right} border: none;">{tot_util}</td>
                    </tr>
                </tbody>
            </table>
            """

            # Enviar correo usando la función de utilidad
            
            # --- SECCIÓN INFERIOR (NOTAS Y FIRMA) ---
            
            # Construir links de acción
            # Nota: Ajustamos las rutas asumiendo una estructura lógica en el frontend nuevo
            link_si = f"{frontend_url}/autorizar?oc={oc}&token=SI&user={usuario}"
            link_no = f"{frontend_url}/autorizar?oc={oc}&token=NO&user={usuario}"
            link_fuera_si = f"http://190.131.218.34/autorizar?oc={oc}&token=FUERA_SI&user={usuario}"
            link_fuera_no = f"http://190.131.218.34/autorizar?oc={oc}&token=FUERA_NO&user={usuario}"

            # Estilos adicionales
            style_links = "color: #0000EE; text-decoration: underline; font-weight: bold; font-family: Arial, sans-serif; font-size: 14px; margin: 0 5px;"
            style_firma_table = "width: 100%; margin-top: 20px; font-family: Arial, sans-serif; font-size: 12px; border: none;"
            
            # Nombre del usuario creador (si está disponible)
            nombre_creador = datos_oc.get("usuario_oc", {}).get("des_usuario", usuario)

            tabla_html += f"""
            </table>
            
            <!-- NOTAS -->
            <div style="margin-top: 10px; font-family: Arial, sans-serif; font-size: 12px; font-weight: bold;">
                NOTAS: {comentario}
            </div>

            <!-- SECCIÓN DE FIRMA Y AUTORIZACIÓN -->
            <table style="{style_firma_table}">
                <tr>
                    <td style="width: 40%; vertical-align: top; padding-top: 20px;">
                        <strong>Elaborado por:</strong>&nbsp;&nbsp;
                        <span style="text-decoration: underline;">{nombre_creador}/Negociador</span>
                        <br><br><br>
                        <div style="text-align: center; border-top: 1px solid #000; width: 80%; margin: 0 auto; padding-top: 5px;">
                            Nombre/Cargo
                        </div>
                    </td>
                    <td style="width: 20%; vertical-align: top; padding-top: 20px; text-align: right; font-weight: bold;">
                        Autorizar:
                    </td>
                    <td style="width: 40%; vertical-align: top; padding-top: 20px;">
                        <div>
                            <a href="{link_si}" style="{style_links}">Si</a> / 
                            <a href="{link_no}" style="{style_links}">No</a>
                        </div>
                        <br>
                        <div style="font-weight: bold;">
                            Opcion Fuera Oficina:
                        </div>
                        <div>
                            <a href="{link_fuera_si}" style="{style_links}">Si</a> / 
                            <a href="{link_fuera_no}" style="{style_links}">No</a>
                        </div>
                        <br><br>
                        <div style="text-align: center; border-top: 1px solid #000; width: 80%; margin: 0 auto; padding-top: 5px;">
                            Firma
                        </div>
                    </td>
                </tr>
            </table>
            """

            resultado = self.enviar_correo_autorizacion(
                oc=oc,
                de=de,
                para=para,
                bcc=bcc,
                cuerpo_url=cuerpo_url,
                tabla_items=tabla_html
            )
            
            if resultado:
                return self.tools.output(
                    200, 
                    "Solicitud de autorización enviada correctamente.", 
                    {"oc": oc}
                )
            else:
                raise CustomException("Error al enviar el correo de autorización.")
                
        except CustomException as e:
            print(f"Error al solicitar autorización: {e}")
            raise CustomException(f"{e}")

    # Query para enviar correo de autorización
    def enviar_correo_autorizacion(self, oc: str, de: str, para: list, bcc: list, cuerpo_url: str, tabla_items: str = ""):
        """
        Envía correo de autorización de orden de compra usando la función de tools.py
        """
        try:
            
            asunto = f"Autorizacion Orden de Compra No. {oc}"
            
            # Cuerpo del mensaje (HTML)
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; }}
                    h3 {{ color: #0056b3; }}
                    a {{ color: #007bff; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <h3>Solicitud de Autorizaci&oacute;n de Orden de Compra</h3>
                <br>
                {tabla_items}
                <br>
            </body>
            </html>
            """
            
            # Enviar a cada destinatario usando la función de tools
            for destinatario in para:
                self.tools.send_email_individual(
                    to_email=destinatario,
                    cc_emails=bcc,
                    subject=asunto,
                    body=html,
                    logo_path=None,
                    mail_sender=de
                )
            
            print(f"Correo de autorización enviado exitosamente para OC {oc}")
            return True
                
        except Exception as e:
            print(f"Error al enviar correo de autorización: {e}")
            return True

    def obtener_detalle_kit(self, data: dict):
        """
        Obtiene el detalle del kit para mostrar en modal.
        Replica la lógica de search_kit.asp
        """
        oc = data["oc"]
        codigo = data["codigo"]
        dolar = float(data.get("dolar", 0) or 0)
        euro = float(data.get("euro", 0) or 0)

        try:
            # 1. Obtener pedido asociado al item en la OC
            pedido = self.querys.obtener_pedido_de_oc(oc, codigo)
            if not pedido:
                # Si no encuentra pedido, devolver estructura vacía segura
                return self.tools.output(200, "No se encontró pedido asociado.", {
                    "info": {"pedido": "N/A", "codigo_kit": codigo},
                    "items": [],
                    "totales": {"costo_total_pesos": 0, "precio_venta_total": 0, "rentabilidad": 0}
                })

            # 1.5 Validar si el código es un hijo de un Kit (Buscar Padre)
            # Lógica ASP: Si es hijo, buscamos el padre para traer todo el grupo.
            codigo_kit = codigo
            padre = self.querys.obtener_padre_kit(pedido, codigo)
            if padre:
                codigo_kit = padre

            # 2. Obtener raw data del kit
            raw_items = self.querys.obtener_datos_kit(pedido, codigo_kit)

            # 3. Procesar items y calcular
            items_procesados = []
            costototalpesos = 0.0
            precioventatotal = 0.0
            
            # Buscar la cantidad del kit (padre) para base de cálculos
            kit_qty = 0.0
            
            # Primero buscamos el item padre
            for it in raw_items:
                if str(it["codigo"]).strip() == str(codigo_kit).strip():
                    kit_qty = float(it["cantidad_ped"] or 0)
                    break
            
            c = 0
            for it in raw_items:
                c += 1
                moneda = str(it["moneda_gen"])
                
                # Valores base desde la query
                cantidad_ped = float(it["cantidad_ped"] or 0) # Para visualización
                cantidad_x_kit = float(it["cantidad_x_kit"] or 0)
                valor_unit = float(it["valor_unit"] or 0)
                costo_unit = float(it["costo"] or 0)
                
                # Cantidad para cálculo (Lógica ASP: CantidadKit * CantidadComponentePorKit)
                cantidad_calculo = cantidad_x_kit * kit_qty

                sub_valor_tot_kit = 0.0
                sub_costo_tot_kit = 0.0
                sub_costo_tot_kit_p = 0.0  # En pesos
                desc_moneda = "Peso"

                # Lógica ASP:
                base_calc = valor_unit * cantidad_calculo
                costo_calc = costo_unit * cantidad_calculo

                if moneda in ["1", "None", ""]:
                    sub_valor_tot_kit = base_calc
                    sub_costo_tot_kit = costo_calc
                    sub_costo_tot_kit_p = costo_calc
                    desc_moneda = "Peso"
                
                elif moneda in ["2", "4", "6", "7"]:
                    sub_valor_tot_kit = base_calc
                    sub_costo_tot_kit = costo_calc
                    sub_costo_tot_kit_p = costo_calc * dolar
                    desc_moneda = "Dolar"
                
                elif moneda in ["3", "5"]:
                    sub_valor_tot_kit = base_calc
                    sub_costo_tot_kit = costo_calc
                    sub_costo_tot_kit_p = costo_calc * euro
                    desc_moneda = "Euro"

                # Acumulados
                costototalpesos += sub_costo_tot_kit_p
                precioventatotal += sub_valor_tot_kit

                items_procesados.append({
                    "c": c,
                    "codigo": it["codigo"],
                    "descripcion": it["descripcion"],
                    "cantidad_ped": cantidad_ped,
                    "cantidad_x_kit": cantidad_x_kit,
                    "valor_unit": valor_unit,
                    "costo_unit": costo_unit,
                    "costo_total": sub_costo_tot_kit,
                    "moneda": desc_moneda,
                    "costo_total_pesos": sub_costo_tot_kit_p,
                    "precio_venta_total": sub_valor_tot_kit
                })

            # 4. Calcular rentabilidad
            rentabilidad = 0.0
            if precioventatotal != 0:
                rentabilidad = ((precioventatotal - costototalpesos) / precioventatotal) * 100
            
            totales = {
                "costo_total_pesos": costototalpesos,
                "precio_venta_total": precioventatotal,
                "rentabilidad": rentabilidad
            }
            
            info_kit = {
                "pedido": pedido, 
                "codigo_kit": codigo_kit, 
                "codigo_consultado": codigo
            }

            return self.tools.output(200, "Detalle del kit obtenido.", {
                "info": info_kit,
                "items": items_procesados,
                "totales": totales
            })

        except Exception as e:
            print(f"Error al obtener detalle kit: {e}")
            raise CustomException(f"{e}")

    def autorizar_oc(self, data: dict):
        """
        Autoriza o Rechaza una orden de compra, envía correos y registra el evento.
        Replica la lógica de autorizar.asp
        """
        oc = data["oc"]
        token = data["token"] # SI / NO
        usuario = data["user"]
        
        # Mapear token a valor esperado por BD (S o N - Aunque ASP usa lo que venga, pero lógica interna es S=Autoriza)
        autoriza = "N"
        if token == "SI":
            autoriza = "S"
        elif token == "NO":
            autoriza = "N"
            
        try:
            # 1. Obtener valor total para registro (Requerido por tabla Distru_Autorizacion_Compra)
            valor_total = self.querys.obtener_valor_total_oc(oc)
            
            # 2. Registrar en base de datos
            # Obtener IP desde el controlador y resolver nombre de host
            client_ip = data.get("client_ip", "")
            equipo = client_ip # Por defecto la IP
            try:
                # Intentar resolver el nombre del host (DNS Inverso)
                if client_ip:
                     host_info = socket.gethostbyaddr(client_ip)
                     # Obtener solo el nombre del equipo
                     full_hostname = host_info[0]
                     equipo = full_hostname.split('.')[0]
            except Exception:
                # Si falla la resolución, se queda con la IP
                pass

            if not equipo: 
                equipo = "WEB_APP_UNKNOWN"

            self.querys.registrar_autorizacion(oc, autoriza, usuario, equipo, valor_total)
            
            # 3. Preparar correo de notificación
            asunto = f"Autorizacion Orden de Compra No. {oc}"
            cuerpo = ""
            
            if autoriza == "S":
                cuerpo = f"La orden de compra No. {oc} fue autorizada. Imprimir la orden desde el 0401"
            else:
                cuerpo = f"La orden de compra No. {oc} no fue autorizada. Favor revisar la orden segun las recomendaciones enviadas por correo."
            
            # Destinatarios (Replica autorizar.asp)
            para = [
                # "compras@avantika.com.co",
                # "direccion.abastecimiento@avantika.com.co",
                # "negociador3@avantika.com.co",
                # "negociador4@avantika.com.co",
                # "negociador1@avantika.com.co"
                "sistemas@avantika.com.co"
            ]
            
            if usuario == "CONTADOR":
                para = ["contador@avantika.com.co"]
                
            # de = "gerencia@avantika.com.co"
            de = "auxiliartic@avantika.com.co"
            bcc = ["sistemas@avantika.com.co"]
            
            # Enviar correo
            for destinatario in para:
                self.tools.send_email_individual(
                    to_email=destinatario,
                    cc_emails=bcc,
                    subject=asunto,
                    body=cuerpo,
                    logo_path=None,
                    mail_sender=de
                )
                
            return self.tools.output(200, "Proceso de autorización realizado correctamente.", {})

        except Exception as e:
            print(f"Error en autorizar_oc: {e}")
            raise CustomException(f"Error al procesar autorización: {e}")
