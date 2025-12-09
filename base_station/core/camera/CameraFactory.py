from camera.IpCamera import IpCamera


class CameraFactory:

    def newCamera(camera_type: str, config: dict):
        if camera_type == "ip_camera":
            ip = config.get('ip_address')
            port = config.get('port')
            username = config.get('username', '')
            password = config.get('password', '')
            
            if username and password:
                url = f"http://{username}:{password}@{ip}:{port}/video"
            else:
                url = f"http://{ip}:{port}/video"
            
            return IpCamera(url)
        elif camera_type == "usb_camera":
            device_id = config.get('device_id',''),
            
            return IpCamera(int(device_id[0])) if device_id else None
    
