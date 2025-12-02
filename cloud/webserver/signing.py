from cryptography.hazmat.primitives.serialization import load_ssh_private_key, load_ssh_public_key
import multibase


def sign_proof(message, private_key_, public_key_):
    # Load the private key
    private_key_object = load_ssh_private_key(private_key_, password=None, )

    # Sign the message
    signature = private_key_object.sign(message.encode('utf-8'))

    return signature


def verify_proof(signature, public_key_, message):
    # Verify the signature
    public_key_object = load_ssh_public_key(public_key_)
    try:
        public_key_object.verify(signature, message.encode('utf-8'))
        return True
    except Exception as e:
        return False


# Example usage
if __name__ == "__main__":
    print('nothing here yet')