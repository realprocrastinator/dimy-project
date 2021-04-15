# Std modules
from collections import defaultdict
import time
from hashlib import sha256
import logging
from threading import Lock
import os
import sys
from pathlib import Path  # if you haven't already done so

# include root src tree path to the sys path so that we can use absolute import
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

# Add toor dir of the src tree to the syspath, so that we can use absolute import
from utils.helpers import ephid_bytes_or_hexstr_to_decimal, ephid_decimal_to_bytes
from idmng.shamir import make_shares, recover_secret
from commn.msg import Message
from commn.udpmgr import UDPManager
import sslcrypto_client as sslcrypto

# A bit hacky here.
# TODO(Jiawei):
# 1) Make it more generic, considering inheret from the original lib.
# 2) Configurable logger
# 3) Add multipthreaded test case
# 4) Consider integrate sslcrypto module into the project instead of using it as a site package
DEFAULT_LOGFILE = "log.txt"

class IDManager(UDPManager):
  """
  By default we are going to use secp128r1 to generate the EC, and private_key, public_key etc.
  """

  def __init__(self, loglevel=logging.DEBUG):
    super().__init__()
    self._curve = sslcrypto.ecc.get_curve("secp128r1")
    self._private_secret = None
    self._public_secret = None

    # those are bytes type
    self._private_secret_bytes = None
    self._EphID = None
    self._EncntID = None

    # we need a lock here to be thread safe
    self.EphID_lock = Lock()
    self.EncntID_lock = Lock()

    # bookkeeping for other clients' secret parts
    # key is the hash_tag, value is a list of EphID
    self.contact_book = defaultdict(list)

    # filter hash tag, we are doing broadcasting, so need to filter out
    # out own message, but it can be useful to utilize self broadcasted message when debugging.
    # TODO(1) periodically clean it up, but as we gen EphID every 10 mins
    # assume we run the app 365 days without terminating, intotal the gernerated hash
    # occupies 365 * 24 * 60 / 10 * 3 / 1014 -> 150kb should be fine.
    self.my_hash_tag = set()

    # logger
    logging.basicConfig(filename=DEFAULT_LOGFILE, filemode="a", \
        format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
    self.logger = logging.getLogger("IDManager")
    shdlr = logging.StreamHandler(sys.stdout)
    shdlr.setLevel(logging.INFO)
    if (not self.logger.handlers):
      self.logger.addHandler(shdlr)
    self.logger.setLevel(loglevel)

  # This function should be only used internally

  def _gen_private_secret(self, is_compressed=True):
    if not self._curve:
      self.logger.error("No selected curve.")
      return None

    self._private_secret = self._curve.new_private_key(is_compressed)

    return self._private_secret

  def gen_EphID(self):
    if (not self._curve):
      self.logger.error("No selected curve.")
      # explicitly clear the EphID to indicate an error occured
      self._EphID = None
      return None

    self.logger.debug("Generating a new EphID and Generating private secret.")
    # Generate the private secret for the ECDH
    self._private_secret = self._gen_private_secret()
    if (not self._private_secret):
      self.logger.error("Failed to generate private secret.")
      # explicitly clear the EphID to indicate an error occured
      self._EphID = None
      return None

    # Convert the insatnce into bytearray type
    self._private_secret_bytes = bytes(self._private_secret)
    self.logger.debug(f"Private secrete is: {self._private_secret_bytes.hex()}")

    self.logger.debug(f"Generating public secret aka EphID.")
    self._public_secret = self._curve.private_to_public(self._private_secret)

    self.logger.debug(f"Assigning new EphID.")

    # make this method thread safe to prevent another thread from trying to
    # retrieve EphiD during generating
    if not self.EphID_lock.locked():
      self.EphID_lock.acquire()

    # The library uses first byte to indicate whether compressed! We ignore it
    self._EphID = bytes(self._public_secret)[1:]

    if (not self._EphID):
      self.logger.error("Failed to generate public secret.")
      # explicitly clear the EphID to indicate an error occured
      self._EphID = None
      return None

    if self.EphID_lock.locked():
      self.EphID_lock.release()
    self.logger.info(f"Newly generated EphID is: {self._EphID.hex()}")

    return self._EphID

  # Use the compressed method when generating points of the curve
  def gen_EncntID(self, other_ephid):
    if (not self._curve):
      self.logger.error("No selected curve.")
      return None

    if (not self._EphID):
      self.logger.error("No EphID is generated.")
      return None

    self.logger.debug("Reconstructing the encounter ID.")
    # make this method thread safe so if another thread trying to retrive Encounter ID,
    # we will be fine
    if not self.EncntID_lock.locked():
      self.EncntID_lock.acquire()

    # According to the sslcrypto lib, the first byte can be either 0x2 or 0x03, we add 0x2 here ;D
    other_public_secret = bytes(b"\x02") + other_ephid
    self._EncntID = self._curve.derive(self._private_secret,
                                       other_public_secret)

    if (not self._EncntID):
      self.logger.error("Failed to generate encounter ID.")
      # explicitly clear the EncntID to indicate an error occured
      self._EncntID = None
      return None

    if self.EncntID_lock.locked():
      self.EncntID_lock.release()

    self.logger.info(f"Newly generated EncntID is: {self._EncntID.hex()}")

    return self._EncntID

  @property
  def EphID(self):

    if not self.EphID_lock.locked():
      self.EphID_lock.acquire()

    EphID = self._EphID

    if self.EphID_lock.locked():
      self.EphID_lock.release()

    return EphID

  @EphID.setter
  def EphID(self, id):

    if not self.EphID_lock.locked():
      self.EphID_lock.acquire()

    self._EphID = id

    if self.EphID_lock.locked():
      self.EphID_lock.release()

  @property
  def EncntID(self):

    if not self.EncntID_lock.locked():
      self.EncntID_lock.acquire()

    EncntID = self._EncntID

    if self.EncntID_lock.locked():
      self.EncntID_lock.release()

    return EncntID

  @EncntID.setter
  def EncntID(self, id):

    if not self.EncntID_lock.locked():
      self.EncntID_lock.acquire()

    self._EncntID = id

    if self.EncntID_lock.locked():
      self.EncntID_lock.release()

  # This function should be called after gen_EphID
  def share_EphID(self, ephid, interval, ip, port, parts=6, threadshold=3):

    # construct six parts using shmair algo
    self.logger.info(f"Generating {parts} sharings of EphID: 0x{ephid.hex()}")
    _, shares = make_shares(ephid_bytes_or_hexstr_to_decimal(ephid),
                            threadshold, parts)

    msg = Message()
    hash_tag_len = msg._tag_len

    # hex string type
    hash_tag = sha256(ephid if isinstance(ephid, bytes) else ephid.
                      encode("utf-8")).hexdigest()[:hash_tag_len * 2]

    # book keeping my hash tag
    self.my_hash_tag.add(hash_tag)

    hash_tag = bytes.fromhex(hash_tag)

    # for each part
    for i, s in shares:
      bsecret = ephid_decimal_to_bytes(s)
      self.logger.info(f"Sharing: 0x{bsecret.hex()}...part: {i}/{parts} ====>")

      # construct the message
      sec_id = hex(i)[2:]
      sec_id = bytes.fromhex(sec_id.zfill(2 * (len(sec_id) + 1 // 2)))
      msg.msg = (hash_tag, sec_id, bsecret)

      # broadcast
      self.send_msg(ip, port, msg.msg)

      # sleep interval seconds
      time.sleep(interval)

  # Reutrn the ecounter ID if possible, otherwise None
  def wait_for_secret(self, ip, port, threshold, bufsz=1024, filter_self=True):
    # Get the message
    msg = Message(msg=self.recv_msg(bufsz=bufsz))

    # UNmarshel the message
    hash_tag, sec_id, secret = msg.tag, msg.sec_id, msg.secret

    if (hash_tag.hex() in self.my_hash_tag and filter_self):
      self.logger.debug("Filter out my own secret share")
      return None

    self.logger.info("\n------------------> Segment 3 <------------------")
    self.logger.info(
        f"Receive: part {int(sec_id.hex(), 16)}, secret: {secret.hex()} from: {hash_tag.hex()} <====="
    )

    # insert into the contact_book, which is only be used in this thread
    self.contact_book[hash_tag.hex()].append(
        (int(sec_id.hex(), 16), int(msg.secret.hex(), 16)))

    secret_shares = self.contact_book[hash_tag.hex()]
    # Check if can perform reconstruction
    if (len(secret_shares) >= threshold):
      self.logger.info("\n------------------> Segment 4 <------------------")
      self.logger.info(
          f"Received {len(secret_shares)} parts now reconstructing the EphID using the first three"
      )

      # Reconstruct EphID in bytes type
      ephid_of_other = ephid_decimal_to_bytes(recover_secret(secret_shares[:3]))
      new_hash_tag = sha256(ephid_of_other if isinstance(ephid_of_other, bytes
                                                        ) else ephid_of_other.
                            encode("utf-8")).hexdigest()[:len(hash_tag) * 2]

      self.logger.info(f"Reconstructed EphID is: 0x{ephid_of_other.hex()} with hash tag 0x{new_hash_tag}")

      if (new_hash_tag != hash_tag.hex()):
        self.logger.error(f"Hash of reconstructed EphID mismatched")
        return None

      self.logger.info(f"Hash of reconstructed EphID matched: {new_hash_tag} == {hash_tag.hex()}")

      encntid = self.gen_EncntID(ephid_of_other)
      del self.contact_book[hash_tag.hex()]

    else:

      self.logger.debug(
          f"Received {len(secret_shares)} parts not enoungh to reconst the EphID"
      )
      encntid = None

    return encntid


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
