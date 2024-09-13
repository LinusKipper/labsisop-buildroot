import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
import os

HOST_NAME = '127.0.0.1'
PORT_NUMBER = 8000

# Funções para coletar as informações do sistema
def get_system_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_uptime():
    with open("/proc/uptime", "r") as f:
        uptime_seconds = float(f.readline().split()[0])
    return uptime_seconds

def get_cpu_info():
    with open("/proc/cpuinfo", "r") as f:
        cpu_model = ""
        cpu_speed = ""
        for line in f:
            if "model name" in line:
                cpu_model = line.split(":")[1].strip()
            if "cpu MHz" in line:
                cpu_speed = line.split(":")[1].strip() + " MHz"
    return cpu_model, cpu_speed

def get_cpu_usage():
    with open("/proc/stat", "r") as f:
        line = f.readline().split()
        total_time = sum(map(int, line[1:]))
        idle_time = int(line[4])
    return 100 - (idle_time / total_time * 100)

def get_memory_info():
    with open("/proc/meminfo", "r") as f:
        mem_total = int(f.readline().split()[1]) // 1024
        mem_free = int(f.readline().split()[1]) // 1024
    mem_used = mem_total - mem_free
    return mem_total, mem_used

def get_system_version():
    with open("/proc/version", "r") as f:
        version = f.readline().strip()
    return version

def get_process_list():
    processes = []
    for pid in os.listdir('/proc'):
        if pid.isdigit():
            try:
                with open(f'/proc/{pid}/comm', 'r') as f:
                    name = f.readline().strip()
                    processes.append((pid, name))
            except FileNotFoundError:
                continue
    return processes

def get_disk_info():
    disks = []
    with open("/proc/partitions", "r") as f:
        for line in f.readlines()[2:]:
            parts = line.split()
            if len(parts) == 4:
                disks.append((parts[3], int(parts[2]) // 1024))
    return disks

def get_usb_devices():
    usb_devices = []
    usb_path = '/sys/bus/usb/devices/'
    
    if os.path.exists(usb_path):
        for device in os.listdir(usb_path):
            device_path = os.path.join(usb_path, device)
            if os.path.isdir(device_path):
                try:
                    with open(os.path.join(device_path, 'product'), 'r') as f:
                        product = f.readline().strip()
                    with open(os.path.join(device_path, 'manufacturer'), 'r') as f:
                        manufacturer = f.readline().strip()
                    usb_devices.append({'device': device, 'product': product, 'manufacturer': manufacturer})
                except FileNotFoundError:
                    continue
    
    # Se nenhum dispositivo USB foi encontrado, retornar uma mensagem apropriada
    if not usb_devices:
        usb_devices.append({'device': 'Nenhum dispositivo USB encontrado', 'product': '', 'manufacturer': ''})
    
    return usb_devices

def get_network_info():
    network_info = []
    with open("/proc/net/dev", "r") as f:
        for line in f.readlines()[2:]:
            parts = line.split()
            network_info.append((parts[0].strip(':'), parts[1], parts[9]))
    return network_info

# Manipulador de requisições HTTP
class MyHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        """Respond to a GET request."""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        cpu_model, cpu_speed = get_cpu_info()
        mem_total, mem_used = get_memory_info()
        processes = get_process_list()
        disks = get_disk_info()
        usb_devices = get_usb_devices()  # Atualizado
        network_adapters = get_network_info()

        # Gerar a resposta HTML
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Informações do Sistema</title>
        </head>
        <body>
            <h1>Informações do Sistema</h1>
            <p><b>Data e Hora:</b> {get_system_time()}</p>
            <p><b>Uptime:</b> {get_uptime()} segundos</p>
            <p><b>Processador:</b> {cpu_model} ({cpu_speed})</p>
            <p><b>Uso do Processador:</b> {get_cpu_usage():.2f}%</p>
            <p><b>Memória:</b> {mem_used} MB usada de {mem_total} MB</p>
            <p><b>Versão do Sistema:</b> {get_system_version()}</p>
            <h2>Processos em Execução</h2>
            <ul>
        """
        for pid, name in processes:
            html += f"<li>{pid}: {name}</li>"

        html += "</ul><h2>Discos</h2><ul>"
        for disk, size in disks:
            html += f"<li>{disk}: {size} MB</li>"

        # Exibir dispositivos USB
        html += "</ul><h2>Dispositivos USB</h2><ul>"
        for device in usb_devices:
            if device['manufacturer'] and device['product']:
                html += f"<li>{device['manufacturer']} - {device['product']} ({device['device']})</li>"
            else:
                html += f"<li>{device['device']}</li>"

        # Exibir adaptadores de rede
        html += "</ul><h2>Adaptadores de Rede</h2><ul>"
        for adapter, rx, tx in network_adapters:
            html += f"<li>{adapter} - RX: {rx} bytes, TX: {tx} bytes</li>"

        html += "</ul></body></html>"

        # Enviar a resposta ao navegador
        self.wfile.write(html.encode('utf-8'))

# Configurar e rodar o servidor
if __name__ == '__main__':
    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
    print("Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))