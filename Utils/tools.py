# import base64
# from Utils.constants import BASE_PATH_TEMPLATE
from fastapi.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
# import json
import os
import base64
import requests
import pytz
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Cargar variables de entorno
load_dotenv()

class Tools:

    def outputpdf(self, codigo, file_name, data={}):
        response = Response(
            status_code=codigo,
            content=data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={file_name}"
            }
        )
        return response


    """ Esta funcion permite darle formato a la respuesta de la API """
    def output(self, codigo, message, data={}):

        response = JSONResponse(
            status_code=codigo,
            content=jsonable_encoder({
                "code": codigo,
                "message": message,
                "data": data,
            }),
            media_type="application/json"
        )
        return response

    # """ Esta funcion permite obtener el template """
    # def get_content_template(self, template_name: str):
    #     template = f"{BASE_PATH_TEMPLATE}/{template_name}"

    #     content = ""
    #     with open(template, 'r') as f:
    #         content = f.read()

    #     return content

    def result(self, msg, code=400, error="", data=[]):
        return {
            "body": {
                "statusCode": code,
                "message": msg,
                "data": data,
                "Exception": error
            }
        }

    # Función para formatear las fechas    
    def format_date(self, date, normal_format, output_format):
        fecha_objeto = datetime.strptime(date, normal_format)
        fecha_formateada = fecha_objeto.strftime(output_format)
        return fecha_formateada

    # Función para formatear las fechas    
    def format_date2(self, date):
        # Convertir la cadena a un objeto datetime
        fecha_objeto = datetime.fromisoformat(date)
        # Formatear la fecha al formato deseado
        fecha_formateada = fecha_objeto.strftime("%d-%m-%Y")
        return fecha_formateada
    
    # Función para formatear fechas con zona horaria
    def format_datetime(self, dt_str):
        dt = datetime.strptime(
            dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        local_dt = dt.astimezone(pytz.timezone('America/Bogota'))
        return local_dt.strftime("%d-%m-%Y %H:%M:%S")
    
    # Función para formatear a dinero    
    def format_money(self, value: str):
        value = value.replace(",", "")
        valor_decimal = Decimal(value)
        return valor_decimal

    def _get_graph_token_and_url(self):
        """Obtiene el access token de Graph (desde BD si está vigente) y la URL base de Graph."""
        from Config.db import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            # Verificar si hay un token vigente en BD
            row = conn.execute(text(
                "SELECT TOP 1 token, fecha_vencimiento "
                "FROM dbo.intranet_graph_token WHERE estado = 1 ORDER BY id DESC"
            )).fetchone()

            # Obtener credenciales siempre (necesitamos la URL de Graph y datos de autenticación)
            rows = conn.execute(text(
                "SELECT nombre, valor FROM dbo.intranet_graph_credenciales"
            )).fetchall()
            creds = {r[0]: r[1] for r in rows}
            graph_url = creds.get("MICROSOFT_URL_GRAPH", "https://graph.microsoft.com/v1.0/users/")

            if row and row[1] > datetime.now():
                return row[0], graph_url

            # Token vencido o inexistente: solicitar uno nuevo
            token_url = f"{creds['MICROSOFT_URL']}{creds['MICROSOFT_TENANT_ID']}/oauth2/v2.0/token"
            resp = requests.post(token_url, data={
                "grant_type": "client_credentials",
                "client_id": creds["MICROSOFT_CLIENT_ID"],
                "client_secret": creds["MICROSOFT_CLIENT_SECRET"],
                "scope": "https://graph.microsoft.com/.default"
            })
            resp.raise_for_status()
            token_json = resp.json()
            new_token = token_json["access_token"]
            expires_at = datetime.now() + timedelta(seconds=token_json.get("expires_in", 3600) - 300)

            # Desactivar tokens anteriores y guardar el nuevo
            conn.execute(text("UPDATE dbo.intranet_graph_token SET estado = 0 WHERE estado = 1"))
            conn.execute(text(
                "INSERT INTO dbo.intranet_graph_token (token, fecha_vencimiento, estado) "
                "VALUES (:t, :fv, 1)"
            ), {"t": new_token, "fv": expires_at})
            conn.commit()

            return new_token, graph_url

    # Función para enviar correos electrónicos
    def send_email_individual(self, to_email, cc_emails, subject, body, logo_path=None, mail_sender=None):
        """Envía un correo electrónico usando Microsoft Graph API."""
        try:
            access_token, graph_url = self._get_graph_token_and_url()
        except Exception as ex:
            print(f"Error obteniendo token de Graph: {ex}")
            return

        send_url = f"{graph_url}{mail_sender}/sendMail"

        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": [{"emailAddress": {"address": to_email}}],
                "ccRecipients": [
                    {"emailAddress": {"address": cc}} for cc in cc_emails
                ] if cc_emails else []
            }
        }

        # Adjuntar el logo como imagen inline si está disponible
        if logo_path:
            try:
                with open(logo_path, 'rb') as img:
                    logo_b64 = base64.b64encode(img.read()).decode('utf-8')
                message["message"]["attachments"] = [{
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": "logo.png",
                    "contentType": "image/png",
                    "contentBytes": logo_b64,
                    "isInline": True,
                    "contentId": "company_logo"
                }]
            except Exception as e:
                print(f"Error adjuntando el logo: {e}")

        try:
            response = requests.post(
                send_url,
                json=message,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            if response.status_code == 202:
                print(f"Correo enviado a {to_email} con copia a {', '.join(cc_emails)}")
            else:
                print(f"Error al enviar correo: {response.status_code} - {response.text}")
        except Exception as ex:
            print(f"Error al enviar correo a {to_email}: {ex}")


    # """ Obtener archivo"""
    # def get_file_b64(self, file_path):
    #     with open(file_path, "rb") as file:
    #         # Leer el contenido binario del archivo PDF
    #         pdf_content = file.read()

    #         # Codificar el contenido binario en base64
    #         pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

    #         return pdf_base64

    # async def send_email_error(self, service_name, code, request, response):
    #     load_dotenv()
    #     # Obtener enviroment
    #     stage = os.getenv("STAGE")
    #     remitente = os.getenv("EMAIL_USER")
    #     destinatario = os.getenv("EMAIL_DEV")

    #     template_url = f"{BASE_PATH_TEMPLATE}/notificacion_error.html"
    #     # Preapar el asunto del correo
    #     subject = f"TOYO - Project: Error service - Stage: {stage}"
    #     # Preparar el contenido del correo
    #     data_correo = {
    #         "servicio": "TOYO",
    #         "status_code": code,
    #         "consumo": service_name,
    #         "id_gestion": "000",
    #         "url": "Toyo_dev",
    #         "request": request,
    #         "response": response
    #     }

    #     msg = MIMEMultipart()
    #     msg["Subject"] = subject
    #     msg["From"] = remitente
    #     msg["To"] = destinatario

    #     with open(template_url, 'r') as template_file:
    #         template = template_file.read()
    #         template = template.format(**data_correo)
    #     msg.attach(MIMEText(template, 'html'))

    #     # Configura la conexión al servidor SMTP de Gmail
    #     server = smtplib.SMTP('smtp.gmail.com', 587)
    #     server.starttls()
    #     server.login(remitente, os.getenv('EMAIL_PASSWORD'))

    #     # Envía el correo
    #     server.sendmail(remitente, destinatario, msg.as_string())

    #     # Cierra la conexión con el servidor SMTP
    #     server.quit()

    # async def send_email(self, recipients, subject, body, attachments=None):
    #     sender = os.getenv("EMAIL_USER")

    #     msg = MIMEMultipart()
    #     msg["Subject"] = subject
    #     msg["From"] = sender
    #     msg["To"] = recipients

    #     msg.attach(MIMEText(body, 'html'))
    #     # Agregar archivos adjuntos en formato base64 al mensaje MIME
    #     if attachments:
    #         for attachment in attachments:
    #             # Decodificar el contenido base64
    #             decoded_data = base64.b64decode(attachment["file"])

    #             # Crear un objeto MIMEBase y adjuntar el archivo decodificado
    #             attachment_part = MIMEBase('application', 'octet-stream')
    #             attachment_part.set_payload(decoded_data)
    #             encoders.encode_base64(attachment_part)

    #             # Establecer el encabezado del archivo adjunto
    #             attachment_part.add_header('Content-Disposition', f'attachment; filename={attachment["name"]}')
    #             msg.attach(attachment_part)

    #     # Configurar conexion con servidor SMTP
    #     server = smtplib.SMTP('smtp.gmail.com', 587)
    #     server.starttls()
    #     server.login(sender, os.getenv('EMAIL_PASSWORD'))
    #     server.sendmail(sender, recipients, msg.as_string())
    #     # Cerrar conexion Con servidor
    #     server.quit()


class CustomException(Exception):
    """ Esta clase hereda de la clase Exception y permite
        interrumpir la ejecucion de un metodo invocando una excepcion
        personalizada """
    def __init__(self, message="", codigo=400, data={}):
        self.codigo = codigo
        self.message = message
        self.data = data
        self.resultado = {
            "body": {
                "statusCode": codigo,
                "message": message,
                "data": data,
                "Exception": "CustomException"
            }
        }