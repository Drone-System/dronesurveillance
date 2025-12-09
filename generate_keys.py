import os
import subprocess

# --- CONFIG ---
current_path = os.path.join(os.path.dirname(__file__))
print(current_path)

proxy_out_dir = current_path + "/cloud/proxy/credentials"
webserver_out_dir = current_path + "/cloud/webserver/credentials"
basestation_out_dir = current_path + "/base_station/core/credentials"

dirs = [proxy_out_dir, webserver_out_dir, basestation_out_dir]

for dir in dirs:
    print(dir)
    os.makedirs(dir, exist_ok=True)

ca_key_core     = os.path.join(current_path, "ca_core.key")
ca_crt_core      = os.path.join(current_path, "ca_core.crt")
ca_srl_core      = os.path.join(current_path, "ca_core.srl")

ca_key_webserver     = os.path.join(current_path, "ca_ws.key")
ca_crt_webserver     = os.path.join(current_path, "ca_ws.crt")
ca_srl_webserver     = os.path.join(current_path, "ca_ws.srl")

server_key_1 = os.path.join(proxy_out_dir, "server_basestation.key")
server_csr_1 = os.path.join(proxy_out_dir, "server_basestation.csr")
server_crt_1 = os.path.join(proxy_out_dir, "server_basestation.crt")

server_key_2 = os.path.join(proxy_out_dir, "server_webserver.key")
server_csr_2 = os.path.join(proxy_out_dir, "server_webserver.csr")
server_crt_2 = os.path.join(proxy_out_dir, "server_webserver.crt")

servername = input("Server host name: ")
webserver_hostname = input("Server host name for webserver: ")

# --- COMMANDS ---
cmds = [
    ["openssl", "genrsa", "-out", ca_key_core, "4096"],
    ["openssl", "req", "-x509", "-new", "-nodes", "-key", ca_key_core,
     "-sha256", "-days", "3650", "-out", ca_crt_core, "-subj", "/CN=MyCA"],

    ["openssl", "genrsa", "-out", server_key_1, "4096"],
    ["openssl", "req", "-new", "-key", server_key_1, "-out", server_csr_1,
     "-subj", f"/CN={servername}"],

    ["openssl", "x509", "-req", "-in", server_csr_1, "-CA", ca_crt_core,
     "-CAkey", ca_key_core, "-CAcreateserial",
     "-out", server_crt_1, "-days", "3650", "-sha256"],

    ["openssl", "genrsa", "-out", ca_key_webserver, "4096"],
    ["openssl", "req", "-x509", "-new", "-nodes", "-key", ca_key_webserver,
     "-sha256", "-days", "3650", "-out", ca_crt_webserver, "-subj", "/CN=MyCA"],

    ["openssl", "genrsa", "-out", server_key_2, "4096"],
    ["openssl", "req", "-new", "-key", server_key_2, "-out", server_csr_2,
     "-subj", f"/CN={webserver_hostname}"],

    ["openssl", "x509", "-req", "-in", server_csr_2, "-CA", ca_crt_webserver,
     "-CAkey", ca_key_webserver, "-CAcreateserial",
     "-out", server_crt_2, "-days", "3650", "-sha256"]
]

# --- RUN ---
for c in cmds:
    subprocess.run(c, check=True)

# --- COPY CA TO 3 LOCATIONS ---

os.makedirs(webserver_out_dir, exist_ok=True)
dest = os.path.join(webserver_out_dir, "ca.crt")

print(dest)
with open(ca_crt_webserver, "rb") as src, open(dest, "wb") as dst:
    dst.write(src.read())


os.makedirs(basestation_out_dir, exist_ok=True)
dest = os.path.join(basestation_out_dir, "ca.crt")

print(dest)
with open(ca_crt_core, "rb") as src, open(dest, "wb") as dst:
    dst.write(src.read())



for f in [ca_crt_webserver, ca_key_webserver, ca_srl_webserver, ca_srl_core, ca_crt_core, ca_key_core]:
    if os.path.exists(f):
        os.remove(f)

