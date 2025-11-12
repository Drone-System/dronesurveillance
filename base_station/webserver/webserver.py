from flask import Flask, render_template, request
import subprocess, ipaddress, netifaces, platform, threading, queue

from config import app, db
from models import Drone, Camera, Protocol

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

# Ping a single IP
def ping_ip(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", param, "1", "-W", "0.1", str(ip)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception:
        return False

# Scan all IPs in the subnet
def scan_network(network):
    alive_ips = []
    q = queue.Queue()

    def worker():
        while True:
            ip = q.get()
            if ip is None:
                break
            if ping_ip(ip):
                alive_ips.append(str(ip))
            q.task_done()

    threads = []
    for _ in range(50):  # 50 threads for faster scanning
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for ip in network.hosts():
        q.put(ip)

    q.join()

    for _ in threads:
        q.put(None)
    for t in threads:
        t.join()

    return alive_ips

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_drone', methods=['GET', 'POST'])
def add_drone():
    if request.method == 'POST':
        ip = request.form.get('ip')
        protocol_name = request.form.get('protocol')

        # Check if the protocol exists, otherwise create it
        protocol = Protocol.query.filter_by(name=protocol_name).first()
        if not protocol:
            protocol = Protocol(name=protocol_name)
            db.session.add(protocol)
            db.session.commit()

        # Create a new Drone record
        new_drone = Drone(ip=ip, name=f"Drone-{ip}", protocol=protocol, model="Tello Boost", status="idle")
        db.session.add(new_drone)
        db.session.commit()

        return f"✅ Drone added successfully with IP {ip} using {protocol_name} protocol!"

    #network = get_local_network()
    #ips = scan_network(network) if network else []
    return render_template('add_device.html', device_type="Drone", ips=["Drone1"], protocols=PROTOCOLS)


@app.route('/add_camera', methods=['GET', 'POST'])
def add_camera():
    if request.method == 'POST':
        ip = request.form.get('ip')
        protocol_name = request.form.get('protocol')

        protocol = Protocol.query.filter_by(name=protocol_name).first()
        if not protocol:
            protocol = Protocol(name=protocol_name)
            db.session.add(protocol)
            db.session.commit()

        new_camera = Camera(ip=ip, name=f"Camera-{ip}", protocol=protocol, resolution="1080p", fps=30)
        db.session.add(new_camera)
        db.session.commit()

        return f"✅ Camera added successfully with IP {ip} using {protocol_name} protocol!"

    #network = get_local_network()
    #ips = scan_network(network) if network else []
    return render_template('add_device.html', device_type="Camera", ips=["Camera1"], protocols=PROTOCOLS)

if __name__ == '__main__':
    app.run(debug=True)
