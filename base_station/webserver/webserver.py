from flask import Flask, render_template, request
import subprocess
import ipaddress
import netifaces
import platform
import threading
import queue

app = Flask(__name__)

# Customize your protocol options here
PROTOCOLS = ["HTTP", "RTSP", "MQTT", "Custom"]

# Get the local IP and subnet
def get_local_network():
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            for link in addrs[netifaces.AF_INET]:
                ip = link['addr']
                netmask = link['netmask']
                if ip != "127.0.0.1":
                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                    return network
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_camera', methods=['GET', 'POST'])
def add_camera():
    if request.method == 'POST':
        ip = request.form.get('ip')
        protocol = request.form.get('protocol')
        return f"Camera added with IP {ip} using {protocol} protocol"
    
    # network = get_local_network()
    # ips = scan_network(network) if network else []
    return render_template('add_device.html', device_type="Camera", ips=[], protocols=PROTOCOLS)

@app.route('/add_drone', methods=['GET', 'POST'])
def add_drone():
    if request.method == 'POST':
        ip = request.form.get('ip')
        protocol = request.form.get('protocol')
        return f"Drone added with IP {ip} using {protocol} protocol"
    
    # network = get_local_network()
    # ips = scan_network(network) if network else []
    return render_template('add_device.html', device_type="Drone", ips=[], protocols=PROTOCOLS)

if __name__ == '__main__':
    app.run(debug=True)
