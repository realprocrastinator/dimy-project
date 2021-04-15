import sslcrypto

if __name__ == "__main__":
  curve = sslcrypto.ecc.get_curve("secp128r1")
  print(curve)
  # if compressesd is set to True, 0x1 is appended at the end
  private_key = curve.new_private_key(is_compressed=True)
  print(type(private_key))
  print(len(private_key) - 1)
  print(bytes(private_key))
  public_key = curve.private_to_public(private_key)
  print(len(public_key) - 1)
  ecdh = curve.derive(private_key, public_key)
  print(ecdh.hex())
