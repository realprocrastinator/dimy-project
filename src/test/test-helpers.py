import sys
from pathlib import Path  # if you haven't already done so

# Add toor dir of the src tree to the syspath, so that we can use absolute import
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from utils.helpers import *

if __name__ == "__main__":
  try:
    bytes_or_hexstr_to_decimal("hi", "notbytes")
  except TypeError as e:
    print("Test Invalid input pass.\n")

  assert (bytes_or_hexstr_to_decimal((1234).to_bytes(16, "big"), "bytes") == 1234)
  assert (bytes_or_hexstr_to_decimal((1234).to_bytes(16, "big").hex(), "str") == 1234)

  print("Test bytes_or_hexstr_to_decimal passed\n")

  assert (ephid_bytes_or_hexstr_to_decimal((567856785678567856785678).to_bytes(16, "big")) == 567856785678567856785678)
  assert (ephid_bytes_or_hexstr_to_decimal((567856785678567856785678).to_bytes(16, "big").hex()) == 567856785678567856785678)

  print("Test ephid_bytes_or_hexstr_to_decimal passed\n")

  test_bytes = b"\x78\x3f\x93\xfa\x14\x76\x73\x7d\xc9\x0e"
  assert (ephid_decimal_to_bytes(567856785678567856785678) == bytes(b"\x00" * (16 - len(test_bytes))) + test_bytes)
  assert (ephid_decimal_to_bytes(567856785678567856785678).hex() == "00" * (16 - len(test_bytes)) + hex(567856785678567856785678)[2:])

  print("Test ephid_decimal_to_bytes passed\n")
