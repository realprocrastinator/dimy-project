from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

if __name__ == "__main__":
  curve = ec.SECP256R1()
  private_key = ec.generate_private_key(curve, default_backend())
  print(private_key.key_size)
  public_key = private_key.public_key()
  print(public_key.key_size)
  shared_key = private_key.exchange(ec.ECDH(), public_key)
  print(len(shared_key.hex()))
