import bgwork
import idmng
import bfmng
import commn
import sys
import time
import signal
import argparse

# pylint: disable=unused-wildcard-import
from tasks import *
from config.configure import load_grp03_global_config

###################
# global vriables #
###################

# control the main loop
G_STOPPED = False

######################
# initialize helpers #
######################


# register managers
def init_register_managers(loglevel, logfile):

  bgmgr = bgwork.BackgroundManager(loglevel=loglevel, logfile=logfile)
  idmgr = idmng.IDManager(loglevel=loglevel, logfile=logfile)
  bfmgr = bfmng.BloomFilterManager(loglevel=loglevel, logfile=logfile)

  return bgmgr, idmgr, bfmgr


# install background tasks
def init_install_bgtasks(config):
  bgmgr, idmgr, bfmgr = init_register_managers(config["ALL_LOG_LEVEL"], config["ALL_LOG_FILE"])

  # install bg_gen_and_bdcast_EphID
  task_name, interval, task_hdlr = "EphID-worker", config["BG_GEN_EphID_SECS"], bg_gen_and_bdcast_EphID
  args = (idmgr, config["UDP_SND_IP"], config["UDP_SND_PORT"], config["BG_SHARE_EphID_SECS"])
  kargs = {}
  bg_task_install(bgmgr, task_name, interval, task_hdlr, *args, **kargs)

  # install bg_receive_and_try_reconstruct_EncntID
  task_name, interval, task_hdlr = "EncntID-Worker", config["BG_RECV_CHECK_SECS"], bg_receive_and_try_reconstruct_EcntID
  args = (idmgr, bfmgr, config["UDP_RCV_IP"], config["UDP_RCV_PORT"], config["NUM_THRESHOLD"])
  kargs = {"filter_self" : config["SELF_FILTER"]}
  bg_task_install(bgmgr, task_name, interval, task_hdlr, *args, **kargs)

  # install bg_qbf_woker_combine_and_query
  task_name, interval, task_hdlr = "QBF-Worker", config["BG_QBF_GEN_SECS"], bg_qbf_woker_combine_and_query
  args = (bfmgr, config["URL_TEMPLATE"].format(config["URL_SUFFIX"]["QUERY"]))
  kargs = {}
  bg_task_install(bgmgr, task_name, interval, task_hdlr, *args, **kargs)

  return bgmgr, idmgr, bfmgr


# handle the signal
def sig_handler(signum, frame):
  global G_STOPPED
  print(f"Handling signal: {signum}, trying to terminat the process")
  G_STOPPED = True


def init_register_signal_hdlr():
  # register signal handler for handling signals
  signal.signal(signal.SIGTERM, sig_handler)
  signal.signal(signal.SIGINT, sig_handler)


#################
# Other helpers #
#################

def process_args():
    usage_str = """
    %(prog)s [OPTIONS]"""
    
    epilog_str = """

    """
    parser = argparse.ArgumentParser(description='DIMY client App.',
                            usage=usage_str,
                            epilog=epilog_str)
    parser.add_argument("-c", "--conf", dest="conf_file", default=None,
                        help="Configuration in Json format. (default: %(default)s).")

    parser.add_argument("-n", "--no-self-filter", action="store_true",
                        help="Flag indicates whether to filter out the self broadcasting message.\
                           Can be useful when debugging locally on one machine. (default: %(default)s).")

    return parser



# the main loop
def main(args):
  global G_STOPPED

  parser = process_args()
  args = parser.parse_args()

  # read congiurations
  config = load_grp03_global_config(args.conf_file)
  config["SELF_FILTER"] = not args.no_self_filter

  print("WELCOME TO USE COVID - TRACING APPLICATION - DIMY\n")

  # pylint: disable=unused-variable
  print(f">>>>> Background services start working, client is working on UDP port {config['UDP_SND_PORT']} <<<<<\n")
  bgworker, idmngr, bfmgr = init_install_bgtasks(config)
  
  # bind to the address where we will reveice msg!
  rcv_ip, rcv_port = config["UDP_RCV_IP"], config["UDP_RCV_PORT"]
  idmngr.bind_address(rcv_ip, rcv_port)

  # initialize the signal handler
  init_register_signal_hdlr()

  # explicitly start the EphID genrator first
  print("Starting the root task, generating and broadcasting the EphID")
  snd_ip, snd_port = config["UDP_RCV_IP"], config["UDP_RCV_PORT"]
  share_interval = config["BG_SHARE_EphID_SECS"]
  bg_gen_and_bdcast_EphID(idmngr, snd_ip, snd_port, share_interval)

  # start all background workers
  bgworker.start_all()
  
  while not G_STOPPED:
    cmd = input("User Command>")

    if cmd == "s":
      print("\nTerminating...")
      G_STOPPED = True

    # combine cbf and stop qbf
    if cmd == "c":
      print("\nUploading CBF to the server...")
      url = config["URL_TEMPLATE"].format(config["URL_SUFFIX"]["UPLOAD"])
      nbg_cbf_combine_and_upload(bfmgr, url)
      bgworker.stop_job("QBF-worker")

      # automatic resetart qbf worker after uploading cbf, not required but would be nice to have
      print("\nRestarting the QBF Worker")
      url = config["URL_TEMPLATE"].format(config["URL_SUFFIX"]["QUERY"])
      bgworker.add_job("QBF-worker", 4, True, bg_qbf_woker_combine_and_query, bfmgr, url)
      bgworker.start_job("QBF-worker", if_restart=True)

  # If we are going to return we clean up any way, just in case we have non daemon threads running
  bgworker.stop_all()
  idmngr.sendsock.close()
  idmngr.recvsock.close()

  return 0


if __name__ == "__main__":
  sys.exit(main(sys.argv))