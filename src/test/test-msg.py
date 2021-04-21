import sys
from pathlib import Path  # if you haven't already done so

# Add toor dir of the src tree to the syspath, so that we can use absolute import
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from commn.msg import Message

if __name__ == "__main__":

  # Test new message
  m = Message()
  tag, sec_id, secret = b"hhh", b"\x01", b"\x99" * 16
  m.msg = tag, sec_id, secret
  assert (m.tag == tag)
  assert (m.sec_id == sec_id)
  assert (m.secret == secret)
  print("Test construct new message passed\n")

  # Test reassign new message
  tag, sec_id, secret = b"lll", b"\x02", b"\x66" * 16
  m.msg = tag, sec_id, secret
  assert (m.tag == tag)
  assert (m.sec_id == sec_id)
  assert (m.secret == secret)
  print("Test reassign new message passed\n")

  # constructor
  b = bytes(b"\x88" * 20)
  m = Message(b)
  tag, sec_id, secret = b"\x88" * 3, b"\x88", b"\x88" * 16
  assert (m.tag == tag)
  assert (m.sec_id == sec_id)
  assert (m.secret == secret)
  print("Test constructing from bytes passed")
