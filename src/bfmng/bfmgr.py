from bloomfilter import BloomFilter
from threading import Lock
from uuid import uuid1
from time import monotonic
import logging
import sys

class DBF(BloomFilter):
    def __init__(self):
        super().__init__()
        self._create_time = monotonic()
        self._id = "DBF-" + uuid1().hex

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
        self.dbfpool = [DBF()]
        self.qbf = None
        self.cbf = None
        self.dbfpool_lock = Lock()
        self.cur_dbf = None
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
            self._add_dbf(DBF())    
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
        self.logger.debug(f"Current pool size is {len(self.dbfpool)}")
        return True

    def add_dbf_atomic(self, dbf= None):
        if not dbf:
            dbf = DBF()        
        
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

if __name__ == "__main__":
    # Small unit test here

    # Testing trivial functionalities
    print("Testing construction of BFmngr")
    bfmgr = BloomFilterManager()
    # By default we only construct one DBF
    assert(len(bfmgr.dbfpool) == 1)
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
    bfmgr._rm_dbf(0)
    assert(len(bfmgr.dbfpool) == 0)

    # reject if pool already empty
    assert(bfmgr._rm_dbf(0) == False)
    
    for _ in range(bfmgr.max_poolsz):
        bfmgr._add_dbf(DBF())
    assert(len(bfmgr.dbfpool) == bfmgr.max_poolsz)

    # reject if full
    assert(bfmgr._add_dbf(DBF()) == False)
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

    # test automic add first
    assert(bfmgr.add_dbf_atomic() == True)
    assert(len(bfmgr.dbfpool) == bfmgr.max_poolsz)
    new_id_list = [bdf.id for bdf in bfmgr.dbfpool]
    assert(all(bfmgr.dbfpool[i].id == id_list[i + 1] for i in range(bfmgr.max_poolsz - 1)))

    id_list = [bdf.id for bdf in bfmgr.dbfpool]
    # test update dbf pool
    assert(bfmgr.update_dbfpool_atomic() == True)
    assert(len(bfmgr.dbfpool) == bfmgr.max_poolsz)
    new_id_list = [bdf.id for bdf in bfmgr.dbfpool]
    assert(all(bfmgr.dbfpool[i].id == id_list[i + 1] for i in range(bfmgr.max_poolsz - 1)))

    print("Test atomic methods add/rm/update passed\n")

    # Test multithreaded cases
    assert(not "Not implemented yet")




  
    



    