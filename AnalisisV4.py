import time
import psutil
import socket
import requests
from datetime import datetime
import pyfiglet

print("               ")
# Texto que quieres en el banner
text = "   @franckT"

# Generar el banner usando pyfiglet
banner = pyfiglet.figlet_format(text)
description = "Monitoreo en Tiempo Real de Conexiones de Navegadores"
text_ = "///////////////////////////////"
banner_ = pyfiglet.figlet_format(text_)

print(description)
print("               ")

# Imprimir el banner
print(banner)
# Texto que describe lo que hace la aplicación

# Variable global para almacenar las conexiones anteriores
conexiones_antiguas = {}

def obtener_conexiones():
    conexiones = psutil.net_connections()
    conexiones_activas = []
    for conn in conexiones:
        if conn.family in (socket.AF_INET, socket.AF_INET6):
            if conn.status == psutil.CONN_ESTABLISHED:
                conexiones_activas.append(conn)
            elif conn.status == psutil.CONN_NONE and conn.pid is not None:
                conexiones_activas.append(conn)
    return conexiones_activas

def obtener_navegador(pid):
    exploradores = {
        "chrome": "Chrome",
        "firefox": "Firefox",
        "opera": "Opera",
        "brave": "Brave",
        "msedge": "Edge",
        "safari": "Safari",
        "oracle": "Oracle",
    }
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline = f.read().decode().split('\x00')
            for arg in cmdline:
                for exe, nombre in exploradores.items():
                    if exe in arg.lower():
                        return nombre
        return "Desconocido"
    except (IndexError, FileNotFoundError):
        return "Desconocido"

def obtener_informacion_ip(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        data = response.json()
        hostname=data.get("hostname", "Hostname desconocido")
        city = data.get("city", "Ciudad desconocida")
        region = data.get("region", "Región desconocida")
        country = data.get("country", "País desconocido")
        loc = data.get("loc", "Ubicación desconocida")
        org = data.get("org", "Organización desconocida")
        timezone = data.get("timezone", "Zona horaria desconocida")
        

        ports = []
        for conn in psutil.net_connections():
            if conn.family in (socket.AF_INET, socket.AF_INET6) and conn.status == psutil.CONN_ESTABLISHED:
                if conn.raddr and conn.raddr.ip == ip:
                    ports.append(conn.raddr.port)
  
        
        return f"Hostname: {hostname},Ciudad: {city}, Región: {region}, País: {country}, Ubicación: {loc}, Organización: {org}, Zona Horaria: {timezone}"
    except Exception as e:
        print("Error al obtener información de la IP:", e)
        return "Información no disponible"


def obtener_direccion_ip(nombre_host):
    try:
        direccion_ip = socket.gethostbyname(nombre_host)
        return direccion_ip
    except socket.gaierror as e:
        print(f"Error al obtener la dirección IP para {nombre_host}: {e}")
        return None

def agrupar_por_navegador(conexiones):
    navegadores = {}
    for conn in conexiones:
        navegador = obtener_navegador(conn.pid)
        if navegador not in navegadores:
            navegadores[navegador] = []
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if conn.status == psutil.CONN_NONE:
            ip_local = conn.laddr.ip
            ip_remota = obtener_direccion_ip("google.com")
            ubicacion_remota = obtener_informacion_ip(ip_remota) if ip_remota else "Desconocida"
            registro = f"Fecha y hora: {fecha_hora}, Tipo: Ping, Local: addr(ip='{ip_local}', port={conn.laddr.port}), Remoto: addr(ip='{ip_remota}', port={conn.laddr.port}), {ubicacion_remota}"
            navegadores[navegador].append(registro)
        else:
            ip_local = conn.laddr.ip
            ip_remota = conn.raddr[0] if conn.raddr else "Desconocida"
            ubicacion_remota = obtener_informacion_ip(ip_remota)
            registro = f"Fecha y hora: {fecha_hora}, PID: {conn.pid}, Local: addr(ip='{ip_local}', port={conn.laddr.port}), Remoto: addr(ip='{ip_remota}', port={conn.raddr.port}), {ubicacion_remota}"
            navegadores[navegador].append(registro)
    return navegadores

def guardar_registro(navegadores, nombre_archivo):
    with open(nombre_archivo, "a") as f:
        for navegador, conexiones in navegadores.items():
            f.write(f"=== {navegador} ===\n")
            for conexion in conexiones:
                f.write(f"{conexion}\n")
            f.write("\n")

def main():
    global conexiones_antiguas

    nombre_archivo = input("Ingrese el nombre del archivo para guardar el registro: ")
    print("\n           Presiona Control + C para detener el script           ")
    print(banner_)
    print(" Aguarde ----->   Capturando conexiones. \n")
    try:
        while True:
            conexiones = obtener_conexiones()
            navegadores = agrupar_por_navegador(conexiones)

            guardar_registro(navegadores, nombre_archivo)


            conexiones_nuevas = {navegador: conexiones for navegador, conexiones in navegadores.items() if navegador in conexiones_antiguas}
            conexiones_cambiadas = {navegador: conexiones for navegador, conexiones in conexiones_nuevas.items() if conexiones != conexiones_antiguas[navegador]}
            conexiones_nuevas = {navegador: conexiones for navegador, conexiones in navegadores.items() if navegador not in conexiones_antiguas}

            conexiones_antiguas = {navegador: conexiones for navegador, conexiones in navegadores.items()}


            if conexiones_cambiadas:
                print("\n¡Las siguientes conexiones han cambiado desde la última actualización!")
                for navegador, conexiones in conexiones_cambiadas.items():
                    print(f"=== {navegador} ===")
                    for conexion in conexiones:
                        print(conexion)
                    print()

            time.sleep(5)  

    except KeyboardInterrupt:
        guardar_registro(conexiones_antiguas, nombre_archivo)
        print(f"\nRegistro guardado en {nombre_archivo} - creado por {text}")

if __name__ == "__main__":
    main()
