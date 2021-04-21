# Std modules
from threading import Lock
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
# Not quite sure why pylint is warning unable to load bfmng module :(
#TODO(Jiawei): fix this issue
from bfmng.bloomfilter import BloomFilter
from bfmng.bfmgr import BloomFilterManager, GBF

if __name__ == "__main__":
  # Small unit test here

  # Testing trivial functionalities
  print("Testing construction of BFmngr")
  bfmgr = BloomFilterManager()
  # By default we only construct one DBF
  # assert(len(bfmgr.dbfpool) == 1)
  assert (bfmgr.dbfpool_lock != None)
  assert (bfmgr.dbfpool_lock.locked() == False)
  bfmgr.dbfpool_lock.acquire()
  assert (bfmgr.dbfpool_lock.locked() == True)
  bfmgr.dbfpool_lock.release()
  assert (bfmgr.dbfpool_lock.locked() == False)
  print("Test construction passed\n")

  # Testing add / remove DBF to / from the pool, single threaded
  print("Testing management of BFmngr")
  # Testing primitives
  original_len = len(bfmgr.dbfpool)
  bfmgr._rm_dbf(0)
  assert (len(bfmgr.dbfpool) == original_len - 1)
  # assert(bfmgr.cur_dbf == None)

  # reject if pool already empty
  # assert(bfmgr._rm_dbf(0) == False)

  for _ in range(bfmgr.max_poolsz):
    bfmgr._add_dbf(GBF())
  assert (len(bfmgr.dbfpool) == bfmgr.max_poolsz)
  assert (bfmgr.cur_dbf == bfmgr.dbfpool[-1])

  # reject if full
  assert (bfmgr._add_dbf(GBF()) == False)
  print("Test add/rm primitives passed\n")

  # test atomic methods in single thread case
  # reject if already full
  assert (bfmgr.add_dbf_atomic() == False)
  id_list = [bdf.id for bdf in bfmgr.dbfpool]

  # test automic remove first
  assert (bfmgr.rm_dbf_atomic() == True)
  assert (len(bfmgr.dbfpool) == bfmgr.max_poolsz - 1)
  new_id_list = [bdf.id for bdf in bfmgr.dbfpool]
  assert (all(bfmgr.dbfpool[i].id == id_list[i + 1] for i in range(bfmgr.max_poolsz - 1)))
  assert (bfmgr.cur_dbf == bfmgr.dbfpool[-1])

  # test automic add first
  assert (bfmgr.add_dbf_atomic() == True)
  assert (len(bfmgr.dbfpool) == bfmgr.max_poolsz)
  new_id_list = [bdf.id for bdf in bfmgr.dbfpool]
  assert (all(bfmgr.dbfpool[i].id == id_list[i + 1] for i in range(bfmgr.max_poolsz - 1)))
  assert (bfmgr.cur_dbf == bfmgr.dbfpool[-1])

  id_list = [bdf.id for bdf in bfmgr.dbfpool]
  # test update dbf pool
  assert (bfmgr.update_dbfpool_atomic() == True)
  assert (len(bfmgr.dbfpool) == bfmgr.max_poolsz)
  new_id_list = [bdf.id for bdf in bfmgr.dbfpool]
  assert (all(bfmgr.dbfpool[i].id == id_list[i + 1] for i in range(bfmgr.max_poolsz - 1)))
  assert (bfmgr.cur_dbf == bfmgr.dbfpool[-1])

  # test insert into DBF
  bfmgr.insert_to_dbf("Hello World")
  assert (bfmgr.cur_dbf.contains("Hello World") == True)
  bfmgr.insert_to_dbf("Hello UNSW")
  assert (bfmgr.cur_dbf.contains("Hello UNSW") == True)

  # test cluster dbfs
  assert (not bfmgr.cluster_dbf(bfmgr.max_poolsz + 1, "QBF"))
  assert (not bfmgr.cluster_dbf(-1, "QBF"))
  assert (not bfmgr.cluster_dbf(bfmgr.max_poolsz, "XBF"))

  assert (bfmgr.cluster_dbf(bfmgr.max_poolsz, "QBF"))
  assert (bfmgr.qbf != None)
  assert (bfmgr.qbf.contains("Hello World"))
  assert (bfmgr.qbf.contains("Hello UNSW"))
  assert (bfmgr.qbf.contains("World") == False)
  assert (bfmgr.qbf.contains("UNSW") == False)

  assert (bfmgr.cluster_dbf(bfmgr.max_poolsz, "CBF"))
  assert (bfmgr.cbf != None)
  assert (bfmgr.cbf.contains("Hello World"))
  assert (bfmgr.cbf.contains("Hello UNSW"))
  assert (bfmgr.qbf.contains("World") == False)
  assert (bfmgr.qbf.contains("UNSW") == False)

  print("Test atomic methods add/rm/update/cluster passed\n")

  # Test dump method
  # Invalid case

  # reset the pool and recluster qbf and cbf
  for _ in range(bfmgr.max_poolsz):
    bfmgr.update_dbfpool_atomic()

  bfmgr.cluster_dbf(bfmgr.max_poolsz, "QBF")
  bfmgr.cluster_dbf(bfmgr.max_poolsz, "CBF")
  assert (bfmgr.qbf)
  assert (bfmgr.cbf)

  exp_str = base64.b64encode(bytearray(b"\x00" * (800000 // 8))).decode('utf-8')

  PREFIX = "./dump-b64"

  b64bfstr = bfmgr.dump_bf("xbf", outfile=PREFIX + "qbf")
  assert (not b64bfstr)
  b64bfstr = bfmgr.dump_bf("dbf", idx=-1, outfile=PREFIX + "qbf")
  assert (not b64bfstr)
  b64bfstr = bfmgr.dump_bf("qbf", outfile=PREFIX + "qbf")
  assert (b64bfstr == exp_str)
  b64bfstr = bfmgr.dump_bf("cbf", outfile=PREFIX + "cbf")
  assert (b64bfstr == exp_str)
  b64bfstr = bfmgr.dump_bf("dbf", outfile=PREFIX + "dbf")
  assert (b64bfstr == exp_str)
  b64bfstr = bfmgr.dump_bf("dbf", idx=1, outfile=PREFIX + "dbf-1")
  assert (b64bfstr == exp_str)

  print("Test dump bf using base64 encoding passed\n")

  # Test multithreaded cases
  assert (not "Multithreaded test case not implemented yet")