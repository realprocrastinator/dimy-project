import bgwork
import idmng
import bfmng
import commn
import sys
import time
import signal

# GLOBAL variable section
G_STOPPED = False
G_DEBUG = True

# GLOBAL contants
DEFAULTBDCST_IP = "255.255.255.255"
DEFAULTBDCST_PORT = 8080
DEFAULTLISTENT_IP = ""
DEFAULTSHARE_INTVL = 1
DEFAULTSHARE_PARTS = 6
DEFAULTSHARE_THRSD = 3

# This is a rapid prototyping the program flow
# TODO(Jiawei): 
# 1) Real implementation
# 2) Fix the signal handler
# 3) Once the implementation of other modules done, change print to their logger instead
# 4) Make bg job interval configurable using a json file  
def background_tasks_install():
  bgworker = bgwork.BackgroundWorker()

  # generate EphID every `ephid_gen_interval` s, and share one part every `secret_share_interval` sec
  idmngr = idmng.IDManager()
  ephid_gen_interval = 3
  # assert(ephid_gen_interval > DEFAULTSHARE_INTVL * DEFAULTSHARE_PARTS)
  secret_share_interval = 1
  total_shares = ephid_gen_interval // secret_share_interval

  # register the callback function which will get invloked when the timer fires
  @bgworker.myjob("EphID-sender", ephid_gen_interval, True)
  def gen_and_bdcast_EphID_wrapper():
    ephid = idmngr.gen_EphID()
    if (not ephid):
      idmngr.logger.error("Failed to generat EphID")

    
    # simulate send one share every 2s
    idmngr.logger.debug(f"Broadcasting EphID: {ephid}")
    idmngr.share_EphID(ephid, DEFAULTSHARE_INTVL, DEFAULTBDCST_IP, DEFAULTBDCST_PORT)

  # bind to the address first
  idmngr.bind_address(DEFAULTLISTENT_IP, DEFAULTBDCST_PORT)
  # register the callback function which will
  @bgworker.myjob("EphID-receiver", DEFAULTSHARE_INTVL * DEFAULTSHARE_THRSD, True)
  def receive_and_try_reconstruct_EcntID():
    encntid = idmngr.wait_for_secret(DEFAULTLISTENT_IP, DEFAULTBDCST_PORT, DEFAULTSHARE_THRSD, filter_self = not G_DEBUG)
    if (encntid):
      # insert to the DBF
      idmngr.logger.info("Inserting a new EncntID to the DBF")
      bfmgr.insert_to_dbf(encntid)


  # periodically cleanup the DBF every `dbf_clean_interval` sec
  bfmgr = bfmng.BloomFilterManager()
  dbf_update_interval = 20

  # register the callback function updating DBF pool periodically
  @bgworker.myjob("DBF-worker", dbf_update_interval, True)
  def cleaner_do_job():
    print("Cleaner woke up, doing cleaning")
    print("Updating the DBF pool")
    
    bfmgr.update_dbfpool_atomic()


  # periodically combining 6 DBFs every `qbf_gen_interval` sec
  qbf_gen_interval = 30

  @bgworker.myjob("QBF-worker", qbf_gen_interval, True)
  def qbf_worker_do_job():
    print("QBF worker woke up, doing combining")
    qbf = bfmgr.cluster_dbf(bfmgr.max_poolsz, type_name = "QBF")
    if (qbf):
      print(f"Querying the sever with QBF ID: {qbf.id}")
      
      # TODO(Jiawei): make url configurable
      res, msg = commn.query_qbf(commn.URL.format(commn.suffix["query"]),\
                                 {"QBF" : bfmgr.dump_bf("QBF", bf = qbf)})

      print("Got the result from server: ", res)
      print(msg)

    else:
      print("QBF not ready, may be pool is not full yet?")

  return bgworker, idmngr, bfmgr

# A way to explicitly add a bg task to the bgworker
def qbf_worker_redo_job(mgr):
  print("QBF worker woke up, doing combining")
  qbf = mgr.cluster_dbf(mgr.max_poolsz, type_name = "QBF")
  
  if (qbf):
      print(f"Querying the sever with QBF ID: {qbf.id}")
      
      # TODO(Jiawei): make url configurable
      res, msg = commn.query_qbf(commn.URL.format(commn.suffix["query"]),\
                                 {"QBF" : mgr.dump_bf("QBF", bf = qbf)})

      print("Got the result from server: ", res)
      print(msg)

  else:
      print("QBF not ready, may be pool is not full yet?")
  
  print()


def cbf_combine_and_upload(mgr):
  print("CBF worker woke up, doing combining")
  cbf = mgr.cluster_dbf(mgr.max_poolsz, type_name = "CBF")
  
  if (cbf):
      print(f"Uploading the CBF with ID: {cbf.id}")
      
      # TODO(Jiawei): make url configurable
      res = commn.upload_cbf(commn.URL.format(commn.suffix["upload"]),\
                                 {"CBF" : mgr.dump_bf("CBF", bf = cbf)})

      print("Got the result from server: ", "Success" if res else "Failed")

  else:
      print("QBF not ready, may be pool is not full yet?")
  
  print()
  


# TODO(Jiawei): change global var inside signal handler not working
def sig_handler(signum, frame):
  global G_STOPPED
  print(f"Handling signal: {signum}")
  G_STOPPED = True

def main():
  global G_STOPPED

  # register signal handler for handling signals
  signal.signal(signal.SIGTERM, sig_handler)
  signal.signal(signal.SIGINT, sig_handler)

  bgworker, idmngr, bfmgr = background_tasks_install()
  bgworker.start_all()

  while not G_STOPPED:
    print("This is in the main Thread")
    cmd = input("User Command>")
    
    if cmd == "s":
      G_STOPPED = True
    
    # combine cbf and stop qbf
    if cmd == "c":
      cbf_combine_and_upload(bfmgr)
      bgworker.stop_job("QBF-worker")

    # resetart qbf, not required but would be nice to have
    if cmd == "r":
      print("Restarting the QBF Worker")
      bgworker.add_job("QBF-worker", 4, True, qbf_worker_redo_job, bfmgr)
      bgworker.start_job("QBF-worker", if_restart=True)

  # If we are going to return we clean up any way, just in case we have non daemon threads running
  bgworker.stop_all()

  return 0
  

if __name__ == "__main__":
  sys.exit(main())
  