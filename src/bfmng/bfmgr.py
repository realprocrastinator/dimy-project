# Std modules
from threading import Lock, Condition
from uuid import uuid1
from time import monotonic
import logging
import sys
import base64
import sys
from pathlib import Path  # if you haven't already done so

# Add toor dir of the src tree to the syspath, so that we can use absolute import
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

# Custom modules
from bfmng.bloomfilter import BloomFilter


# A genieric BF calss, can be DBF, QBF or CBF
class GBF(BloomFilter):

  def __init__(self, bf_type="DBF"):
    super().__init__()
    self._create_time = monotonic()
    self._id = bf_type + "-" + uuid1().hex

  @property
  def create_time(self):
    return self._create_time

  @property
  def id(self):
    return self._id

  @id.setter
  def id(self, id):
    self._id = id

  # How long has it been created?
  @property
  def life(self):
    return monotonic() - self._create_time


class BloomFilterManager(object):
  def __init__(self, max_poolsz=6, init_pool_sz = 1, loglevel=logging.DEBUG, logfile=None):
    self.dbfpool = [GBF() for _ in range(init_pool_sz)]
    self._qbf = None
    self._cbf = None
    self.dbfpool_lock = Lock()
    self.dbfpool_cv = Condition()
    self._cur_dbf = self.dbfpool[0]
    self.max_poolsz = max_poolsz
    # The flag indicates whether we should use the last DBF
    # Since the every 10 minutes, we will moving from one to the next DBF,
    # which means after 60 mins we will always point at the last DBF  
    self.use_last = False
    self.cur_dbf_idx = 0

    # logger
    logging.basicConfig(filename=logfile, filemode="a", \
        format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
    self.logger = logging.getLogger("BFManager")
    shdlr = logging.StreamHandler(sys.stdout)
    shdlr.setLevel(logging.INFO)
    shdlr.createLock()
    self.shdlr = shdlr
    if (not self.logger.handlers):
      self.logger.addHandler(shdlr)
    self.logger.setLevel(loglevel)

  # renew_ is thread safe method which does two things
  # 1) Remove the oldest DBF whose TTL > x time
  # 2) Create a new BF in the pool
  # 3) The BF in the poll are ordered by timestamp, from the oldest to the latest
  # 4) Current dbf should always point to the last dbf in dbfpool
  # return True on Success, False on error
  def update_dbfpool_atomic(self):
    if not self.dbfpool_lock.locked():
      self.dbfpool_lock.acquire()

    if (len(self.dbfpool) < self.max_poolsz):
      # No need to remove
      self.add_dbf_atomic()
    elif (len(self.dbfpool) == self.max_poolsz):
      # Remove the head and append to the tail
      self._rm_dbf(0)
      self._add_dbf(GBF())
      # If we updated, then always use the last DBF
      self.use_last = True
    else:
      # This should never happen unless we have a concurrency bug
      self.logger.error(f"Pool Size larger than {self.max_poolsz}! Raise condition here!")
      return False
    
    self.cur_dbf_idx = len(self.dbfpool) - 1

    if self.dbfpool_lock.locked():
      self.dbfpool_lock.release()

    return True

  # Non thread safe method, only call this when no concurrencies!
  def _add_dbf(self, dbf):
    if (len(self.dbfpool) == self.max_poolsz):
      return False

    self.dbfpool.append(dbf)
    # update the current DBF to the latest one
    self._cur_dbf = self.dbfpool[-1]
    self.cur_dbf_idx = len(self.dbfpool) - 1

    self.logger.debug(f"Adding a new DBF to the pool with id {dbf.id}. Now the size is: {len(self.dbfpool)}")
    return True

  def add_dbf_atomic(self, dbf=None):
    if not dbf:
      dbf = GBF()

    res = True

    # astomic add to the pool
    if not self.dbfpool_lock.locked():
      self.dbfpool_lock.acquire()

    res = self._add_dbf(dbf)

    if self.dbfpool_lock.locked():
      self.dbfpool_lock.release()

    return res

  # Non thread safe method, only call this when no concurrencies!
  def _rm_dbf(self, dbf_idx):
    if len(self.dbfpool) == 0 or dbf_idx < 0 or dbf_idx >= self.max_poolsz:
      return False

    self.logger.debug(f"Removing a DBF from the pool with id {self.dbfpool[dbf_idx].id}. Now the size is: {len(self.dbfpool)}")
    del self.dbfpool[dbf_idx]

    self.logger.debug("Updating current DBF")
    if (len(self.dbfpool) > 0):
      # update the current DBF to the latest one
      self._cur_dbf = self.dbfpool[-1]
    else:
      self._cur_dbf = None

    return True

  def rm_dbf_atomic(self, id=None):
    res = True

    if not self.dbfpool_lock.locked():
      self.dbfpool_lock.acquire()

    if not id:
      # remove the oldest DBF from the pool if no id specified
      res = self._rm_dbf(0)
    else:
      if (any(not self._rm_dbf(i) for i, dbf in enumerate(self.dbfpool) if dbf.id == id)):
        res = False

      # explicitly remove a DBF
      # for i, dbf in enumerate(self.dbfpool):
      #     if dbf.id == id:
      #         self._rm_dbf(self.dbfpool[i])

    if self.dbfpool_lock.locked():
      self.dbfpool_lock.release()

    return res

  # cluster a set of bfs into one, type_name can be "QBF" or "CBF"
  def cluster_dbf(self, num, type_name):
    self.logger.info("\n------------------> Segment 8 or 10 <------------------"
                    f"\nClustering {self.max_poolsz} DBFs into one {type_name}\n")

    if num < 0 or num > len(self.dbfpool) or type_name not in ["QBF", "CBF"]:
      self.logger.debug(f"Pool not ready yet")
      return None

    res_bf = GBF(bf_type=type_name)

    if not self.dbfpool_lock.locked():
      self.dbfpool_lock.acquire()

    for i in range(num):
      res_bf.union(self.dbfpool[i])

    if type_name == "QBF":
      self._qbf = res_bf
    else:
      self._cbf = res_bf

    if self.dbfpool_lock.locked():
      self.dbfpool_lock.release()

    return res_bf

  # Thread safe method, get the current DBF
  @property
  def cur_dbf(self):
    # if not self.dbfpool_lock.locked():
    #   self.dbfpool_lock.acquire()

    # if not self.dbfpool_lock.locked():
    #   self.dbfpool_lock.release()

    # We can use week sync, read no can happen either before/after write
    return self._cur_dbf  


  def update_cur_dbf(self):
      if not self.dbfpool_lock.locked():
        self.dbfpool_lock.acquire()

      if (self.use_last):
        cur = self.dbfpool[-1] if len(self.dbfpool) > 0 else None
      else:
        self.cur_dbf_idx += 1
        if (self.cur_dbf_idx >= self.max_poolsz):
          # If we move to the laste one already but update has been called
          # Truncate to the last element 
          self.cur_dbf_idx = self.max_poolsz - 1
        cur = self.dbfpool[self.cur_dbf_idx]

      # update internal cache _cur_dbf
      self._cur_dbf = cur

      if not self.dbfpool_lock.locked():
        self.dbfpool_lock.release()

      return cur     

  # Thread safe method, atomiclly insert a data in to the current DBF
  def insert_to_dbf(self, data):
    if not self.dbfpool_lock.locked():
      self.dbfpool_lock.acquire()

    self._cur_dbf.insert(data)
    self.logger.info(f"\n------------------> Segment 6 & 7-A <------------------"
                     f"\nInserting a new EncntID: {data.hex()} to the DBF (murmur3 hashing with 3 hashes)"
                     f"\nInserting data {data.hex()} into DBF#{self.cur_dbf_idx} with id {self._cur_dbf.id}"
                     f"\nCurrent Bloomfilter {self._cur_dbf.id} state is :{self._cur_dbf.state}")
    # Make sure we dont't have inconsistency
    assert(self.dbfpool[self.cur_dbf_idx] == self._cur_dbf)

    if not self.dbfpool_lock.locked():
      self.dbfpool_lock.release()

  def _get_cluster(self, type_name):
    res = None

    if not self.dbfpool_lock.locked():
      self.dbfpool_lock.acquire()

    self.logger.debug(f"Get the cluster of {type_name}")
    res = self._qbf if type_name == "QBF" else self._cbf

    if not self.dbfpool_lock.locked():
      self.dbfpool_lock.release()

    return res

  # Thread safe method, get QBF
  @property
  def qbf(self):
    return self._get_cluster("QBF")

  # Thread safe method, get CBF
  @property
  def cbf(self):
    return self._get_cluster("CBF")

  # return a raw str encoded using base64, also write to a file if outfile is not None
  # this method is not thread safe! return False on error
  def dump_bf(self, type_name, idx=None, outfile=None, bf=None):
    # if we want to dump an bf passed through argument
    if (bf and isinstance(bf, GBF)):
      bfarr = bytearray(bf.arr)
      b64_str = base64.b64encode(bfarr).decode('utf-8')
      return b64_str
    elif bf:
      raise TypeError("Not BloomFilter type")

    type_name = type_name.lower()

    if (type_name == "qbf") and self._qbf:
      # array type
      bf = bytearray(self._qbf.arr)
      # raw string encoded in base64
      b64_str = base64.b64encode(bf).decode('utf-8')

    elif (type_name == "cbf") and self._cbf:
      bf = bytearray(self.cbf.arr)
      b64_str = base64.b64encode(bf).decode('utf-8')

    elif (type_name == "dbf"):
      if (not idx):
        bf = bytearray(self.cur_dbf.arr)
      else:
        if (idx < 0 or idx >= len(self.dbfpool)):
          self.logger.error("Idx can't be negative or go beyond current max pool size.")
          return False

        bf = bytearray(self.dbfpool[idx].arr)

      b64_str = base64.b64encode(bf).decode('utf-8')

    else:
      self.logger.error("Unsupported BF type or BF not ready yet.")
      return False

    self.logger.debug(f"Dumping {type_name.upper()}.\n" if not outfile else f"to {outfile}.")

    if outfile:
      with open(outfile, "w") as f:
        f.write(b64_str)

    return b64_str

