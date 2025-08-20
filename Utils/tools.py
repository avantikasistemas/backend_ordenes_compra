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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import pytz
from datetime import datetime, timezone
from decimal import Decimal

# Cargar variables de entorno
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 25))

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

    # Función para enviar correos electrónicos
    def send_email_individual(self, to_email, cc_emails, subject, body, logo_path=None, mail_sender=None):
        """Envía un correo electrónico a un destinatario con copia a otros y adjunta un logo si está disponible."""
        msg = MIMEMultipart()
        msg['From'] = mail_sender
        msg['To'] = to_email
        msg['Cc'] = ", ".join(cc_emails) if cc_emails else ""
        msg['Subject'] = subject

        # Agregar el contenido HTML
        msg.attach(MIMEText(body, 'html'))
        
        # Adjuntar el logo si está disponible
        if logo_path:
            try:
                with open(logo_path, 'rb') as img:
                    logo = MIMEImage(img.read())
                    logo.add_header('Content-ID', '<company_logo>')
                    msg.attach(logo)
            except Exception as e:
                print(f"Error adjuntando el logo: {e}")
        
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.sendmail(mail_sender, [to_email] + cc_emails, msg.as_string())
            print(f"Correo enviado a {to_email} con copia a {', '.join(cc_emails)}")
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