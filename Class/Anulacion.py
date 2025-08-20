from Utils.tools import Tools, CustomException
from Utils.querys import Querys
from datetime import datetime
from fastapi import Response
import pandas as pd
from io import BytesIO
import os
from urllib.parse import urljoin
import socket

class Anulacion:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()
        self.querys = Querys(self.db)

    # Función que se encarga de enviar la peticion para anular orden de compra.
    def peticion_anular_orden_compra(self, data: dict):

        try:

            # Validamos el campo usuario
            if not data["usuario"] or data["usuario"] == "null":
                raise CustomException('El campo usuario no puede ser vacio.')

            # Consultamos la información de la orden de compra.
            data_oc = self.querys.check_si_oc_anulada(data["oc"])
            
            # Verificamos si la orden de compra existe.
            if not data_oc:
                raise CustomException('Número de orden de compra no existe.')

            # Verificamos si la orden de compra está anulada.
            if data_oc["anulado"]:
                raise CustomException(
                    'Esta orden de compra ya se encuentra anulada.'
                )

            registro_anulacion = self.querys.consultar_registro_anulacion(data["oc"])
            if registro_anulacion:
                if registro_anulacion["anulado"] == 0:
                    raise CustomException(
                        'Ya existe un proceso de anulación para esta orden de compra.'
                    )
                elif registro_anulacion["anulado"] == 1:
                    raise CustomException(
                        'Esta orden de compra ya se encuentra anulada.'
                    )

            # Guardamos el registro de anulación
            data_anulado = self.querys.guardar_registro_anulacion(data)

            # Asignamos el usuario
            usuario = data["usuario"]

            # Obtenemos el correo del usuario
            mail = self.querys.get_mail_by_username(usuario)

            # Asignamos la variable de entorno de la url del frontend
            base_url = os.getenv("FRONTEND_BASE_URL")

            # Construimos la URL de la anulación
            path = f"/oc/anulaciones/{data_anulado['id']}"

            # Construimos el link completo
            link = urljoin(base_url.rstrip('/')+'/', path.lstrip('/'))

            # Construimos el cuerpo del correo electrónico
            body_email = self.build_anulacion_email_html(data_oc, link, data)
            
            to_email = 'sistemas@avantika.com.co' # Cambiar por gerencia
            # cc_emails = ['compras@avantika.com.co', 'direccion.abastecimiento@avantika.com.co'] # Estos son los correos a enviar en producción.
            cc_emails = ['auxiliartic@avantika.com.co']
            if mail not in cc_emails:
                cc_emails.append(mail)

            self.tools.send_email_individual(
                to_email=to_email,
                cc_emails=cc_emails,
                subject=f"Anulación orden de compra #: {data['oc']}",
                body=body_email,
                logo_path="C:/inetpub/wwwroot/App_Avantika/Mercadeo/clientes_creados_mes/logo.png",
                mail_sender=mail
            )

            # Retornamos la información.
            return self.tools.output(200, "Petición de anulación enviada con éxito.", "")

        except CustomException as e:
            print(f"Error al obtener información de seguimiento: {e}")
            raise CustomException(f"{e}")

    # Función para construir el cuerpo del correo electrónico de anulación
    def build_anulacion_email_html(self, data_oc: dict, link: str, data: dict):

        logo_url = "cid:company_logo"
        # Construir tabla de ítems si existen
        items_html = ""
        oc_detalles = data_oc.get('oc_detalles', [])
        if oc_detalles:
            items_html += """
            <tr>
                <td style='padding:16px 24px 0 24px;'>
                    <div style='font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#111827;font-weight:700;margin-bottom:8px;'>Ítems de la Orden de Compra</div>
                    <table role='presentation' cellpadding='0' cellspacing='0' border='0' width='100%' style='border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;'>
                        <thead>
                            <tr style='background:#f9fafb;'>
                                <th style='font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#374151;font-weight:600;padding:8px 10px;'>Código</th>
                                <th style='font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#374151;font-weight:600;padding:8px 10px;'>Descripción</th>
                                <th style='font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#374151;font-weight:600;padding:8px 10px;'>Cantidad</th>
                                <th style='font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#374151;font-weight:600;padding:8px 10px;'>Valor</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            for item in oc_detalles:
                items_html += f"""
                            <tr>
                                <td style='font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#111827;padding:8px 10px;'>{item.get('codigo', '')}</td>
                                <td style='font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#111827;padding:8px 10px;'>{item.get('item_nombre', '')}</td>
                                <td style='font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#111827;padding:8px 10px;'>{item.get('cantidad', '')}</td>
                                <td style='font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#111827;padding:8px 10px;'>{"${:,.2f}".format(item.get('valor_unitario', 0))}</td>
                            </tr>
                """
            # Fila de total
            valor_total = data_oc.get('valor_total', 0)
            items_html += f"""
                        <tr>
                            <td colspan='3' style='font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#374151;font-weight:700;padding:10px 12px;text-align:right;background:#f9fafb;'>Valor Total OC:</td>
                            <td style='font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#111827;font-weight:700;padding:10px 12px;background:#f9fafb;'>{"${:,.2f}".format(valor_total)}</td>
                        </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
            """
        # Comentario debajo del valor total y antes de los botones
        comentario = data.get('comentario', '')
        comentario_html = ""
        if comentario:
            comentario_html = f"""
            <tr>
                <td style='padding:16px 24px 0 24px;'>
                    <div style='font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#374151;font-weight:700;margin-bottom:4px;'>Comentario:</div>
                    <div style='font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#111827;background:#f9fafb;padding:10px 12px;border-radius:8px;'>{comentario}</div>
                </td>
            </tr>
            """

        # Links con parámetro de acción
        link_aprobar = f"{link}?accion=1"
        link_rechazar = f"{link}?accion=0"

        return f"""\
            <!DOCTYPE html>
            <html lang="es">
                <div style='text-align: left;'>
                    <img src='{logo_url}' alt='Logo Avantika' style='width:150px; max-width:150px;'/>
                </div>
                <head>
                    <meta charset="utf-8">
                    <meta name="x-apple-disable-message-reformatting">
                    <meta name="viewport" content="width=device-width,initial-scale=1">
                    <title>Solicitud de Anulación</title>
                </head>
                <body style="margin:0;padding:0;background:#f4f6f8;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f4f6f8;">
                        <tr>
                        <td align="center" style="padding:24px;">
                            <!-- Card -->
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:1000px;background:#ffffff;border-radius:12px;box-shadow:0 6px 18px rgba(0,0,0,0.06);overflow:hidden;">
                            <!-- Header -->
                            <tr>
                                <td style="padding:24px 24px 0 24px;">
                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                    <tr>
                                    <td valign="middle" style="padding-left:12px;">
                                        <div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#111827;font-weight:700;line-height:1.2;">Avantika</div>
                                        <div style="font-family:Arial,Helvetica,sans-serif;font-size:20px;color:#111827;font-weight:700;line-height:1.3;">
                                        Solicitud de Anulación<br>de Orden de Compra
                                        </div>
                                    </td>
                                    </tr>
                                </table>
                                </td>
                            </tr>

                            <!-- Body -->
                            <tr>
                                <td style="padding:16px 24px 0 24px;">
                                <p style="margin:0 0 12px 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6;color:#111827;">
                                    Estimado/a <strong>Gerencia</strong>,
                                </p>
                                <p style="margin:0 0 16px 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6;color:#374151;">
                                    Por medio de la presente solicito la anulación de la siguiente orden de compra.
                                </p>
                                </td>
                            </tr>

                            <!-- Tabla de detalles -->
                            <tr>
                                <td style="padding:0 24px 0 24px;">
                                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
                                        <tr>
                                            <td style="background:#f9fafb;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#374151;font-weight:600;padding:10px 12px;width:38%;">Orden de Compra:</td>
                                            <td style="font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#111827;padding:10px 12px;">{data_oc['numero']}</td>
                                        </tr>
                                        <tr>
                                            <td style="background:#f9fafb;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#374151;font-weight:600;padding:10px 12px;">Fecha:</td>
                                            <td style="font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#111827;padding:10px 12px;">{data_oc['fecha_hora']}</td>
                                        </tr>
                                        <tr>
                                            <td style="background:#f9fafb;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#374151;font-weight:600;padding:10px 12px;">Proveedor:</td>
                                            <td style="font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#111827;padding:10px 12px;">{data_oc['tercero_nombre']}</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            {items_html}
                            {comentario_html}
                            <!-- CTA -->
                            <tr>
                                <td align="center" style="padding:24px;">
                                <!-- Botones de acción -->
                                <a href="{link_aprobar}"
                                    style="font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:600;text-decoration:none;background:#0d6efd;color:#ffffff;padding:12px 20px;border-radius:8px;display:inline-block;margin-right:10px;">
                                    Aprobar Anulación
                                </a>
                                <a href="{link_rechazar}"
                                    style="font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:600;text-decoration:none;background:#dc3545;color:#ffffff;padding:12px 20px;border-radius:8px;display:inline-block;margin-left:10px;">
                                    Rechazar Anulación
                                </a>
                                <div style="height:8px;line-height:8px;">&nbsp;</div>
                                <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#6b7280;">
                                    Si los botones no funcionan, copia y pega uno de estos enlaces en tu navegador:<br>
                                    <a href="{link_aprobar}" style="color:#0d6efd;text-decoration:underline;word-break:break-all;">Aprobar: {link_aprobar}</a><br>
                                    <a href="{link_rechazar}" style="color:#dc3545;text-decoration:underline;word-break:break-all;">Rechazar: {link_rechazar}</a>
                                </div>
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="padding:0 24px 24px 24px;">
                                <hr style="border:none;border-top:1px solid #e5e7eb;margin:0 0 12px 0;">
                                <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#9ca3af;line-height:1.5;">
                                    Este mensaje fue generado automáticamente. Por favor, no responda a este correo.
                                </p>
                                </td>
                            </tr>
                            </table>
                            <!-- /Card -->
                        </td>
                        </tr>
                    </table>
                </body>
            </html>
        """

    # Función para obtener los datos de la orden de compra
    def validar_anulacion_orden_compra(self, data: dict, ip: str):

        try:
            id = data["id"]
            accion = data["accion"]
            
            datos = self.querys.consultar_registro_anulacion_x_id(id)
            if not datos:
                return self.tools.output(
                    200, "No se encontró el registro de anulación.")

            numero_oc = datos["numero"]
            datos_oc = self.querys.check_si_oc_anulada(numero_oc)
            if datos_oc["anulado"]:
                return self.tools.output(
                    200, "Esta orden de compra ya ha sido anulada.")

            # Asignamos el usuario
            usuario = datos['usuario']
            
            # Obtenemos el correo del usuario
            mail = self.querys.get_mail_by_username(usuario)

            if accion == 0:
                msg_respuesta = f"La anulación ha sido rechazada."
                body_email = self.build_notificacion_email_html(msg_respuesta)
                self.querys.actualizar_registro_anulacion(
                    id, numero_oc, 0, ip)
                
            if accion == 1:
                msg_respuesta = f"La anulación ha sido aprobada."
                self.querys.anular_cabecera_oc(numero_oc)
                self.querys.eliminar_items_oc(numero_oc)
                self.querys.actualizar_registro_anulacion(
                    id, numero_oc, 1, ip)
                
                msg = f"La orden de compra No. {numero_oc} fue aprobada para su anulación."
                body_email = self.build_notificacion_email_html(msg)
                
            to_email = mail
            # cc_emails = ['compras@avantika.com.co', 'direccion.abastecimiento@avantika.com.co'] # Estos son los correos a enviar en producción.
            cc_emails = ['auxiliartic@avantika.com.co', 'sistemas@avantika.com.co']
            if mail not in cc_emails:
                cc_emails.append(mail)

            self.tools.send_email_individual(
                to_email=to_email,
                cc_emails=cc_emails,
                subject=f"Anulación orden de compra #: {numero_oc}",
                body=body_email,
                mail_sender='tic@avantika.com.co' # Cambia por gerencia
            )

            return self.tools.output(200, msg_respuesta)

        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Función para construir el cuerpo del correo electrónico de notificación
    def build_notificacion_email_html(self, mensaje: str):

        return f"""\
            <!DOCTYPE html>
            <html lang="es">
                <head>
                    <meta charset="utf-8">
                    <meta name="x-apple-disable-message-reformatting">
                    <meta name="viewport" content="width=device-width,initial-scale=1">
                    <title>Notificación de Anulación</title>
                </head>
                <body style="margin:0;padding:0;background:#f4f6f8;">
                    <h4>{mensaje}</h4>
                </body>
            </html>
        """
