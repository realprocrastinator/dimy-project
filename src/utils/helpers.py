# can either take bytes type or hex string
def bytes_or_hexstr_to_decimal(s, typename):
  # int in python can handle arbitary large number
  if typename == "bytes":
    return int(s.hex(), 16)
  elif typename == "str":
    return int(s, 16)
  else:
    raise TypeError("Can only handle str or bytes type.")


def ephid_bytes_or_hexstr_to_decimal(ephid, length=16):
  if isinstance(ephid, bytes):
    if (len(ephid) != length):
      raise ValueError(f"EphID must be {length} bytes long")
    return bytes_or_hexstr_to_decimal(ephid, "bytes")

  elif isinstance(ephid, str):
    # hex string takes two bytes to represent a byte in raw hex!
    if (len(ephid) != length * 2):
      raise ValueError(f"EphID must be {length} bytes long")
    return bytes_or_hexstr_to_decimal(ephid, "str")

  else:
    raise TypeError("Can only handle str or bytes type.")


def ephid_decimal_to_bytes(n, length=16):
  if not isinstance(n, int):
    raise TypeError("Can only handle int type.")

  # 128 bit to 16 bytes, since python uses big endian to represent bytes, we respect!
  return n.to_bytes(length, "big")
