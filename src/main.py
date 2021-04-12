import bgwork
import idmng
import sys
import time
import signal

# GLOBAL variable section
G_STOPPED = False

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
  secret_share_interval = 1
  total_shares = ephid_gen_interval // secret_share_interval

  # register the callback function which will get invloked when the timer fires
  @bgworker.myjob("EphID-worker", ephid_gen_interval, True)
  def gen_and_bdcast_EphID_wrapper():
    idmngr.gen_EphID()
    # simulate send one share every 2s
    idmngr.logger.debug(f"Broadcasting EphID: {idmngr.EphID}")
    sent_shares = 0
    while (sent_shares < total_shares):
      idmngr.logger.debug(f"Sending share: {sent_shares + 1}/{total_shares}")
      time.sleep(2)
      sent_shares += 1

  # periodically cleanup the DBF every `dbf_clean_interval` sec
  dbf_clean_interval = 4
  @bgworker.myjob("DBF-worker", dbf_clean_interval, True)
  def cleaner_do_job():
    print("Cleaner woke up, doing cleaning")
    print("Adding a new DBF slot")

  # periodically combining 6 DBFs every `qbf_gen_interval` sec
  qbf_gen_interval = 4
  @bgworker.myjob("QBF-worker", qbf_gen_interval, True)
  def qbf_worker_do_job():
    print("QBF worker woke up, doing combining")
    print("Querying the sever")
    time.sleep(3)
    print("Got the result from server")

  return bgworker, idmngr

# A way to explicitly add a bg task to the bgworker
def qbf_worker_redo_job(msg1, msg2):
  print("QBF worker woke up, doing combining")
  print(msg1, msg2)
  print("Querying the sever")
  time.sleep(3)
  print("Got the result from server")

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

  bgworker, idmngr = background_tasks_install()
  bgworker.start_all()

  while not G_STOPPED:
    print("This is in the main Thread")
    cmd = input("User Command>")
    
    if cmd == "s":
      G_STOPPED = True
    
    # combine cbf and stop qbf
    if cmd == "c":
      print("")
      bgworker.stop_job("QBF-worker")

    # resetart qbf, not required but would be nice to have
    if cmd == "r":
      print("Restarting the QBF Worker")
      bgworker.add_job("QBF-worker", 4, True, qbf_worker_redo_job, "Hello", "World")
      bgworker.start_job("QBF-worker", if_restart=True)

  # If we are going to return we clean up any way, just in case we have non daemon threads running
  bgworker.stop_all()

  return 0
  

if __name__ == "__main__":
  sys.exit(main())
  