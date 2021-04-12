import sys
import os
# A very hacky way to enfore python load a module from the project dir
from pathlib import Path
CURDIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = Path(CURDIR).parent.absolute()
sys.path.append(str(WORKSPACE))
import sslcrypto_client as sslcrypto
from threading import Lock
import logging
import sys

# A bit hacky here. 
# TODO(Jiawei): 
# 1) Make it more generic, considering inheret from the original lib. 
# 2) Configurable logger
# 3) Add multipthreaded test case  
# 4) Consider integrate sslcrypto module into the project instead of using it as a site package 

class IDManager(object):
    """
    By default we are going to use secp128r1 to generate the EC, and private_key, public_key etc.
    """
    def __init__(self, loglevel = logging.DEBUG):
        self._curve = sslcrypto.ecc.get_curve("secp128r1")
        self._private_secret = None
        self._public_secret = None
        
        # those are bytearray type
        self._private_secret_bytes = None
        self._EphID = None
        self._EncntID = None

        # we need a lock here to be thread safe
        self.EphID_lock =  Lock()
        self.EncntID_lock = Lock()

        # logger
        self.logger = logging.getLogger("IDManager")
        shdlr = logging.StreamHandler(sys.stdout)
        shdlr.setLevel(loglevel)
        formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
        shdlr.setFormatter(formatter)
        self.logger.addHandler(shdlr)
        self.logger.setLevel(loglevel)


    # This function should be only used internally
    def _gen_private_secret(self, is_compressed = True):
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
        
        self.logger.debug("Generating a new EphID.")
        self.logger.debug(f"Generating private secret.")

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
        self.EphID_lock.acquire()
        # The library uses first byte to indicate whether compressed! We ignore it
        self._EphID = bytes(self._public_secret)[1:]
        
        if (not self._EphID):
            self.logger.error("Failed to generate public secret.")
            # explicitly clear the EphID to indicate an error occured
            self._EphID = None
            return None
        
        self.EphID_lock.release()
        self.logger.info(f"EphID is: {self._EphID.hex()}")

        return self._EphID
        

    def gen_EncntID(self):
        if (not self._curve):
            self.logger.error("No selected curve.")
            return None

        if (not self._EphID):
            self.logger.error("No EphID is generated.")
            return None

        self.logger.debug("Reconstructing the encounter ID.")
        # make this method thread safe so if another thread trying to retrive Encounter ID,
        # we will be fine
        self.EncntID_lock.acquire()
        self._EncntID = self._curve.derive(self._private_secret, self._public_secret)

        if (not self._EncntID):
            self.logger.error("Failed to generate encounter ID.")
            # explicitly clear the EncntID to indicate an error occured
            self._EncntID = None
            return None

        self.EncntID_lock.release()
        
        self.logger.info(f"EncntID is: {self._EncntID.hex()}")

        return self._EncntID
    
    @property
    def EphID(self):
        
        self.EphID_lock.acquire()
        EphID = self._EphID 
        self.EphID_lock.release()

        return EphID

    @EphID.setter
    def EphID(self, id):
        self.EphID_lock.acquire()
        self._EphID = id
        self.EphID_lock.release()
    
    @property
    def EncntID(self):
        
        self.EncntID_lock.acquire()
        EncntID = self._EncntID 
        self.EncntID_lock.release()

        return EncntID

    @EncntID.setter
    def EncntID(self, id):

        self.EncntID_lock.acquire()
        self._EncntID = id        
        self.EncntID_lock.release()


if __name__ == "__main__":
    
    # small test
    c = IDManager()

    print("Testing invalid cases")    
    # if haven't called gen_EphID then I expected None here
    assert(c.EphID == None)
    # if the EphID is none then we expect gen_EncntID to return None as well
    assert(c.gen_EncntID() == None)
    assert(c.EncntID == None)
    print("Test: Invalid cases passed\n")

    print("Testing whether lib and methods are functioning well")    
    EphID = c.gen_EphID()
    assert(EphID != None)
    assert(EphID == c.EphID)
    assert(isinstance(EphID, bytes))
    assert(isinstance(c.EphID, bytes))
    assert(len(EphID) == 16)
    assert(len(c.EphID) == 16)    
    print("EphID is:", c.EphID.hex())
    print("Test: EphID passed\n")
    
    EncntID = c.gen_EncntID()
    assert(EncntID != None)
    assert(EncntID == c.EncntID)
    assert(isinstance(EncntID, bytes))
    assert(isinstance(c.EncntID, bytes))
    assert(len(EncntID) == 16)
    assert(len(c.EncntID) == 16)
    print("EncntID is:", c.EncntID.hex())
    print("Test: EncntID passed\n")

    # TODO(jiawei): Testing whether locking functions in multithreaded case
    print("Testing multithreaded case")
    assert(not"Not implemented yet\n")



