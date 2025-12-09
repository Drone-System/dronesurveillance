import os


def _load_credential_from_file(filepath):
    real_path = os.path.join(os.path.dirname(__file__), filepath)
    with open(real_path, "rb") as f:
        return f.read()


BS_SERVER_CERTIFICATE = _load_credential_from_file("credentials/server_basestation.crt")
BS_SERVER_CERTIFICATE_KEY = _load_credential_from_file("credentials/server_basestation.key")
#BS_ROOT_CERTIFICATE = _load_credential_from_file("credentials/server_basestation.crt")

WS_SERVER_CERTIFICATE = _load_credential_from_file("credentials/server_webserver.crt")
WS_SERVER_CERTIFICATE_KEY = _load_credential_from_file("credentials/server_webserver.key")
#WS_ROOT_CERTIFICATE = _load_credential_from_file("credentials/server_basestation.crt")