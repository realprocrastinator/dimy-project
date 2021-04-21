import sys
from pathlib import Path  # if you haven't already done so

# Add toor dir of the src tree to the syspath, so that we can use absolute import
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from idmng.idmgr import *

if __name__ == "__main__":
  # small test
  c = IDManager()

  print("Testing invalid cases")
  # if haven't called gen_EphID then I expected None here
  assert (c.EphID == None)
  # if the EphID is none then we expect gen_EncntID to return None as well
  assert (c.gen_EncntID(bytes()) == None)
  assert (c.EncntID == None)
  print("Test: Invalid cases passed\n")

  print("Testing whether lib and methods are functioning well")
  EphID = c.gen_EphID()
  assert (EphID != None)
  assert (EphID == c.EphID)
  assert (isinstance(EphID, bytes))
  assert (isinstance(c.EphID, bytes))
  assert (len(EphID) == 16)
  assert (len(c.EphID) == 16)
  print("EphID is:", c.EphID.hex())
  print("Test: EphID passed\n")

  # Test generating EncntID for c
  c2 = IDManager()
  c2_EphID = c2.gen_EphID()

  c_EncntID = c.gen_EncntID(c2_EphID)
  assert (c_EncntID != None)
  assert (c_EncntID == c.EncntID)
  assert (isinstance(c_EncntID, bytes))
  assert (isinstance(c.EncntID, bytes))
  assert (len(c_EncntID) == 16)
  assert (len(c.EncntID) == 16)
  print("EncntID is:", c.EncntID.hex())

  # Generating EncntID for c2
  c_EphID = EphID
  c2_EncntID = c2.gen_EncntID(c_EphID)
  assert (c.EncntID == c2.EncntID)
  print("Test: EncntID passed\n")

  # Testing broadcasting shares and reconstruct shares
  c.bind_address("", 8080)
  c.share_EphID(c.EphID, 2, "255.255.255.255", 8080)

  for _ in range(6):
    EncntID = c.wait_for_secret("", 8080, 3)
    print(EncntID)

  # If filter on we expect None return
  assert (EncntID == None)

  print("Broadcasting shares and reconstruct shares passed")

  # TODO(jiawei): Testing whether locking functions in multithreaded case
  print("Testing multithreaded case")
  assert (not "Not implemented yet\n")
