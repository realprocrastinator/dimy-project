# Add toor dir of the src tree to the syspath, so that we can use absolute import
import sys
from pathlib import Path # if you haven't already done so
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from bfmng.bloomfilter import BloomFilter
from threading import Lock
from uuid import uuid1
from time import monotonic
import logging
import sys
import base64

# A genieric BF calss, can be DBF, QBF or CBF
class GBF(BloomFilter):
    def __init__(self, bf_type = "DBF"):
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
    def __init__(self, max_poolsz = 6, loglevel = logging.DEBUG):
        self.dbfpool = [GBF() for _ in range(max_poolsz)]
        self._qbf = None
        self._cbf = None
        self.dbfpool_lock = Lock()
        self._cur_dbf = self.dbfpool[-1]
        self.max_poolsz = max_poolsz

        # logger
        self.logger = logging.getLogger("BFManager")
        shdlr = logging.StreamHandler(sys.stdout)
        shdlr.setLevel(loglevel)
        formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
        shdlr.setFormatter(formatter)
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
        else:
            # This should never happen unless we have a concurrency bug
            self.logger.error(f"Pool Size larger than {self.max_poolsz}! Raise condition here!")
            return False

        if self.dbfpool_lock.locked():
            self.dbfpool_lock.release()

        return True
    
    # Non thread safe method, only call this when no concurrencies!
    def _add_dbf(self, dbf):
        if (len(self.dbfpool) == self.max_poolsz):
            return False

        self.logger.debug(f"Adding a new DBF to the pool with id {dbf.id}")        
        self.dbfpool.append(dbf)
        # update the current DBF to the latest one
        self._cur_dbf = self.dbfpool[-1]
        self.logger.debug(f"Current pool size is {len(self.dbfpool)}")
        return True

    def add_dbf_atomic(self, dbf= None):
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

        self.logger.debug(f"Removing a DBF from the pool with id {self.dbfpool[dbf_idx].id}")        
        del self.dbfpool[dbf_idx]
        
        if (len(self.dbfpool) > 0):
            # update the current DBF to the latest one
            self._cur_dbf = self.dbfpool[-1]
        else:
            self._cur_dbf = None

        self.logger.debug(f"Current pool size is {len(self.dbfpool)}")

        return True

    def rm_dbf_atomic(self, id = None):        
        self.logger.debug(f"Removing a DBF from the pool")        
        
        res = True

        if not self.dbfpool_lock.locked():
            self.dbfpool_lock.acquire()

        if not id:                
            # remove the oldest DBF from the pool if no id specified            
            res = self._rm_dbf(0)
        else:
            if (any(not self._rm_dbf(i) for i, dbf in enumerate(self.dbfpool) if dbf.id == id)):
                res = False
            # for i, dbf in enumerate(self.dbfpool):
            #     if dbf.id == id:
            #         self._rm_dbf(self.dbfpool[i])

        if self.dbfpool_lock.locked():
            self.dbfpool_lock.release()

        return res

    # cluster a set of bfs into one, type_name can be "QBF" or "CBF"
    def cluster_dbf(self, num, type_name):
        if num < 0 or num > len(self.dbfpool) or type_name not in ["QBF", "CBF"]:
            return None

        res_bf = GBF(bf_type = type_name)

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
        if not self.dbfpool_lock.locked():
            self.dbfpool_lock.acquire()

        cur = self.dbfpool[-1] if len(self.dbfpool) > 0 else None
        return cur

        if not self.dbfpool_lock.locked():
            self.dbfpool_lock.acquire()

    # Thread safe method, atomiclly insert a data in to the current DBF
    def insert_to_dbf(self, data):
        if not self.dbfpool_lock.locked():
            self.dbfpool_lock.acquire()

        self.logger.debug(f"Inserting data {data} into DBF {self._cur_dbf.id}")
        self.dbfpool[-1].insert(data)

        if not self.dbfpool_lock.locked():
            self.dbfpool_lock.acquire()

    def _get_cluster(self, type_name):
        res = None
        
        if not self.dbfpool_lock.locked():
            self.dbfpool_lock.acquire()

        self.logger.debug(f"Getting {type_name}")
        res = self._qbf if type_name == "QBF" else self._cbf

        if not self.dbfpool_lock.locked():
            self.dbfpool_lock.acquire()

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
    def dump_bf(self, type_name, idx = None, outfile = None, bf = None):
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
        

if __name__ == "__main__":
    # Small unit test here

    # Testing trivial functionalities
    print("Testing construction of BFmngr")
    bfmgr = BloomFilterManager()
    # By default we only construct one DBF
    # assert(len(bfmgr.dbfpool) == 1)
    assert(bfmgr.dbfpool_lock != None)
    assert(bfmgr.dbfpool_lock.locked() == False)
    bfmgr.dbfpool_lock.acquire()
    assert(bfmgr.dbfpool_lock.locked() == True)
    bfmgr.dbfpool_lock.release()
    assert(bfmgr.dbfpool_lock.locked() == False)
    print("Test construction passed\n")

    # Testing add / remove DBF to / from the pool, single threaded 
    print("Testing management of BFmngr")
    # Testing primitives
    original_len = len(bfmgr.dbfpool) 
    bfmgr._rm_dbf(0)
    assert(len(bfmgr.dbfpool) == original_len - 1)
    # assert(bfmgr.cur_dbf == None)

    # reject if pool already empty
    # assert(bfmgr._rm_dbf(0) == False)
    
    for _ in range(bfmgr.max_poolsz):
        bfmgr._add_dbf(GBF())
    assert(len(bfmgr.dbfpool) == bfmgr.max_poolsz)
    assert(bfmgr.cur_dbf == bfmgr.dbfpool[-1])

    # reject if full
    assert(bfmgr._add_dbf(GBF()) == False)
    print("Test add/rm primitives passed\n")

    # test atomic methods in single thread case
    # reject if already full
    assert(bfmgr.add_dbf_atomic() == False)
    id_list = [bdf.id for bdf in bfmgr.dbfpool]
    
    # test automic remove first 
    assert(bfmgr.rm_dbf_atomic() == True)
    assert(len(bfmgr.dbfpool) == bfmgr.max_poolsz - 1)
    new_id_list = [bdf.id for bdf in bfmgr.dbfpool]
    assert(all(bfmgr.dbfpool[i].id == id_list[i + 1] for i in range(bfmgr.max_poolsz - 1)))
    assert(bfmgr.cur_dbf == bfmgr.dbfpool[-1])

    # test automic add first
    assert(bfmgr.add_dbf_atomic() == True)
    assert(len(bfmgr.dbfpool) == bfmgr.max_poolsz)
    new_id_list = [bdf.id for bdf in bfmgr.dbfpool]
    assert(all(bfmgr.dbfpool[i].id == id_list[i + 1] for i in range(bfmgr.max_poolsz - 1)))
    assert(bfmgr.cur_dbf == bfmgr.dbfpool[-1])

    id_list = [bdf.id for bdf in bfmgr.dbfpool]
    # test update dbf pool
    assert(bfmgr.update_dbfpool_atomic() == True)
    assert(len(bfmgr.dbfpool) == bfmgr.max_poolsz)
    new_id_list = [bdf.id for bdf in bfmgr.dbfpool]
    assert(all(bfmgr.dbfpool[i].id == id_list[i + 1] for i in range(bfmgr.max_poolsz - 1)))
    assert(bfmgr.cur_dbf == bfmgr.dbfpool[-1])

    # test insert into DBF
    bfmgr.insert_to_dbf("Hello World")
    assert(bfmgr.cur_dbf.contains("Hello World") == True)
    bfmgr.insert_to_dbf("Hello UNSW")
    assert(bfmgr.cur_dbf.contains("Hello UNSW") == True)

    # test cluster dbfs
    assert(not bfmgr.cluster_dbf(bfmgr.max_poolsz + 1, "QBF"))
    assert(not bfmgr.cluster_dbf(-1, "QBF"))
    assert(not bfmgr.cluster_dbf(bfmgr.max_poolsz, "XBF"))
    
    assert(bfmgr.cluster_dbf(bfmgr.max_poolsz, "QBF"))
    assert(bfmgr.qbf != None)
    assert(bfmgr.qbf.contains("Hello World"))
    assert(bfmgr.qbf.contains("Hello UNSW"))
    assert(bfmgr.qbf.contains("World") == False)
    assert(bfmgr.qbf.contains("UNSW") == False)
    
    assert(bfmgr.cluster_dbf(bfmgr.max_poolsz, "CBF"))
    assert(bfmgr.cbf != None)
    assert(bfmgr.cbf.contains("Hello World"))
    assert(bfmgr.cbf.contains("Hello UNSW"))
    assert(bfmgr.qbf.contains("World") == False)
    assert(bfmgr.qbf.contains("UNSW") == False)


    print("Test atomic methods add/rm/update/cluster passed\n")

    # Test dump method
    # Invalid case

    # reset the pool and recluster qbf and cbf
    for _ in range(bfmgr.max_poolsz):
        bfmgr.update_dbfpool_atomic()

    bfmgr.cluster_dbf(bfmgr.max_poolsz, "QBF")
    bfmgr.cluster_dbf(bfmgr.max_poolsz, "CBF")
    assert(bfmgr.qbf)
    assert(bfmgr.cbf)

    exp_str = base64.b64encode(bytearray(b"\x00" * (800000 // 8))).decode('utf-8')
    
    PREFIX = "./dump-b64"

    b64bfstr = bfmgr.dump_bf("xbf", outfile = PREFIX + "qbf")
    assert(not b64bfstr)
    b64bfstr = bfmgr.dump_bf("dbf", idx = -1, outfile = PREFIX + "qbf")
    assert(not b64bfstr)
    b64bfstr = bfmgr.dump_bf("qbf", outfile = PREFIX + "qbf")
    assert(b64bfstr == exp_str)
    b64bfstr = bfmgr.dump_bf("cbf", outfile = PREFIX + "cbf")
    assert(b64bfstr == exp_str)
    b64bfstr = bfmgr.dump_bf("dbf", outfile = PREFIX + "dbf")
    assert(b64bfstr == exp_str)
    b64bfstr = bfmgr.dump_bf("dbf", idx = 1, outfile = PREFIX + "dbf-1")
    assert(b64bfstr == exp_str)
    
    print("Test dump bf using base64 encoding passed\n")

    # Test multithreaded cases
    assert(not "Multithreaded test case not implemented yet")




  
    



    