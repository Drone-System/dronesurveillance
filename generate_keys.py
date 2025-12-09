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

ca_key     = os.path.join(current_path, "ca.key")
ca_crt     = os.path.join(current_path, "ca.crt")
ca_srl     = os.path.join(current_path, "ca.srl")
server_key = os.path.join(proxy_out_dir, "server.key")
server_csr = os.path.join(proxy_out_dir, "server.csr")
server_crt = os.path.join(proxy_out_dir, "server.crt")

servername = input("Server host name: ")

# --- COMMANDS ---
cmds = [
    ["openssl", "genrsa", "-out", ca_key, "4096"],
    ["openssl", "req", "-x509", "-new", "-nodes", "-key", ca_key,
     "-sha256", "-days", "3650", "-out", ca_crt, "-subj", "/CN=MyCA"],

    ["openssl", "genrsa", "-out", server_key, "4096"],
    ["openssl", "req", "-new", "-key", server_key, "-out", server_csr,
     "-subj", f"/CN={servername}"],

    ["openssl", "x509", "-req", "-in", server_csr, "-CA", ca_crt,
     "-CAkey", ca_key, "-CAcreateserial",
     "-out", server_crt, "-days", "3650", "-sha256"]
]

# --- RUN ---
for c in cmds:
    subprocess.run(c, check=True)

# --- COPY CA TO 3 LOCATIONS ---
for target in dirs:
    os.makedirs(target, exist_ok=True)
    dest = os.path.join(target, "ca.crt")
    print(dest)
    with open(ca_crt, "rb") as src, open(dest, "wb") as dst:
        dst.write(src.read())

for f in [ca_crt, ca_key, ca_srl]:
    if os.path.exists(f):
        os.remove(f)


print("Generated:")
print(ca_crt)
print(server_key)
print(server_crt)
