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
  ephid_gen_interval = 7
  # assert(ephid_gen_interval > DEFAULTSHARE_INTVL * DEFAULTSHARE_PARTS)

  # register the callback function which will get invloked when the timer fires
  @bgworker.myjob("EphID-sender", ephid_gen_interval, True)
  # pylint: disable=unused-variable
  def gen_and_bdcast_EphID_wrapper():
    idmngr.logger.info("\n------------------> Segment 1 & 2 <------------------")
    idmngr.logger.info(">>>>>>  Generating and broadcasting secrets   <<<<<<<")

    ephid = idmngr.gen_EphID()
    if (not ephid):
      idmngr.logger.error("Failed to generat EphID")

    # simulate send one share every 2s
    idmngr.share_EphID(ephid, DEFAULTSHARE_INTVL, DEFAULTBDCST_IP, DEFAULTBDCST_PORT)

  # bind to the address first
  idmngr.bind_address(DEFAULTLISTENT_IP, DEFAULTBDCST_PORT)
  # register the callback function which will
  @bgworker.myjob("EphID-receiver", 1.5 * DEFAULTSHARE_INTVL * DEFAULTSHARE_THRSD, True)
  # pylint: disable=unused-variable
  def receive_and_try_reconstruct_EcntID():
    encntid = idmngr.wait_for_secret(DEFAULTLISTENT_IP, DEFAULTBDCST_PORT, DEFAULTSHARE_THRSD, filter_self=not G_DEBUG)

    idmngr.logger.info("\n------------------> Segment 5 <------------------")
    idmngr.logger.info(f">>>> generate shared secret EncID: {encntid} <<<<")
    if (encntid):
      # insert to the DBF
      bfmgr.logger.info("\n------------------> Segment 6 & 7 <------------------")
      bfmgr.logger.info("Inserting a new EncntID to the DBF (murmur3 hashing with 3 hashes)")
      bfmgr.insert_to_dbf(encntid)

  # periodically cleanup the DBF every `dbf_clean_interval` sec
  bfmgr = bfmng.BloomFilterManager()
  dbf_update_interval = 20

  # register the callback function updating DBF pool periodically
  @bgworker.myjob("DBF-worker", dbf_update_interval, True)
  # pylint: disable=unused-variable
  def cleaner_do_job():
    print("\nUpdating the DBF pool...Removing the oldest DBF and add a new DBF")

    bfmgr.update_dbfpool_atomic()

  # periodically combining 6 DBFs every `qbf_gen_interval` sec
  qbf_gen_interval = 30

  @bgworker.myjob("QBF-worker", qbf_gen_interval, True)
  # pylint: disable=unused-variable
  def qbf_worker_do_job():
    bfmgr.logger.info("\n------------------> Segment 8 & 9 <------------------")
    qbf = bfmgr.cluster_dbf(bfmgr.max_poolsz, type_name="QBF")
    if (qbf):

      bfmgr.logger.info(f"Querying the sever with QBF ID: {qbf.id}")

      # TODO(Jiawei): make url configurable
      res, msg = commn.query_qbf(commn.URL.format(commn.suffix["query"]),\
                                 {"QBF" : bfmgr.dump_bf("QBF", bf = qbf)})

      bfmgr.logger.info("\n\n=============================")
      bfmgr.logger.info(f"Got the result from server: {res}")
      bfmgr.logger.info(msg)
      bfmgr.logger.info("=============================\n\n")

    else:
      bfmgr.logger.info("QBF not ready, may be pool is not full yet?")

  return bgworker, idmngr, bfmgr


# A way to explicitly add a bg task to the bgworker
def qbf_worker_redo_job(mgr):
  qbf = mgr.cluster_dbf(mgr.max_poolsz, type_name="QBF")

  if (qbf):
    mgr.logger.info(f"Querying the sever with QBF ID: {qbf.id}")

    # TODO(Jiawei): make url configurable
    res, msg = commn.query_qbf(commn.URL.format(commn.suffix["query"]),\
                               {"QBF" : mgr.dump_bf("QBF", bf = qbf)}, log_func=mgr.logger.debug)

    mgr.logger.info("\n\n=============================")
    mgr.logger.info(f"Got the result from server: {res}")
    mgr.logger.info(msg)
    mgr.logger.info("=============================\n\n")

  else:
    mgr.logger.info("QBF not ready, may be pool is not full yet?")

  mgr.logger.info("\n")


def cbf_combine_and_upload(mgr):
  mgr.logger.info("\n------------------> Segment 10 <------------------")

  cbf = mgr.cluster_dbf(mgr.max_poolsz, type_name="CBF")

  if (cbf):
    # TODO(Jiawei): make url configurable
    res = commn.upload_cbf(commn.URL.format(commn.suffix["upload"]),\
                               {"CBF" : mgr.dump_bf("CBF", bf = cbf)}, log_func=mgr.logger.debug)

    mgr.logger.info("\n\n=============================")
    mgr.logger.info(f"Got the result from server: {'Success' if res else 'Failed'}")
    mgr.logger.info("=============================\n\n")

  else:
    mgr.logger.info("CBF not ready, may be pool is not full yet?")

  mgr.logger.info("\n")


# TODO(Jiawei): change global var inside signal handler not working
def sig_handler(signum, frame):
  global G_STOPPED
  print(f"Handling signal: {signum}")
  G_STOPPED = True


def main():
  print("WELCOME TO USE COVID - TRACING APPLICATION - DIMY\n\n")

  global G_STOPPED

  # register signal handler for handling signals
  signal.signal(signal.SIGTERM, sig_handler)
  signal.signal(signal.SIGINT, sig_handler)

  # pylint: disable=unused-variable
  bgworker, idmngr, bfmgr = background_tasks_install()
  print(f">>>>> Background services start working, client is working on UDP port {8080} <<<<<\n")
  bgworker.start_all()

  while not G_STOPPED:
    cmd = input("User Command>")

    if cmd == "s":
      print("\nTerminating...")
      G_STOPPED = True

    # combine cbf and stop qbf
    if cmd == "c":
      print("\nUploading CBF to the server...")
      cbf_combine_and_upload(bfmgr)
      bgworker.stop_job("QBF-worker")

    # resetart qbf, not required but would be nice to have
    if cmd == "r":
      print("\nRestarting the QBF Worker")
      bgworker.add_job("QBF-worker", 4, True, qbf_worker_redo_job, bfmgr)
      bgworker.start_job("QBF-worker", if_restart=True)

  # If we are going to return we clean up any way, just in case we have non daemon threads running
  bgworker.stop_all()

  return 0


if __name__ == "__main__":
  sys.exit(main())
