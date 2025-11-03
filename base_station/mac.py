import psutil

for name, addrs in psutil.net_if_addrs().items():
    for addr in addrs:
        if addr.family == psutil.AF_LINK:  # MAC address
            print(f"{name}: {addr.address}")
            
            if name == 'Wi-Fi':
                mac = addr.address

print(mac)
