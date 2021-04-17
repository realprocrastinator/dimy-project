import sys
from pathlib import Path  # if you haven't already done so

# Add toor dir of the src tree to the syspath, so that we can use absolute import
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from commn.udpmgr import UDPManager

# default configurations
DEFAULTBDCST_IP = "255.255.255.255"
DEFAULTBDCST_PORT = 8080
DEFAULTLISTENT_IP = ""
DEFAULT_LOGFILE = "log.txt"

if __name__ == "__main__":
  import threading
  import time

  # A same socket can handle both send and receive
  cli = UDPManager("cli", logfile=DEFAULT_LOGFILE)
  cli.bind_address(DEFAULTLISTENT_IP, DEFAULTBDCST_PORT)

  def cli_tsk():
    while True:
      cli.send_msg(DEFAULTBDCST_IP, DEFAULTBDCST_PORT, b"Hello World")
      time.sleep(2)

  def svr_tsk():
    while True:
      cli.recv_msg()

  t1 = threading.Thread(name="cli", target=cli_tsk)
  t2 = threading.Thread(name="svr", target=svr_tsk)

  t3 = threading.Thread(name="cli", target=cli_tsk)
  t4 = threading.Thread(name="cli", target=cli_tsk)

  t1.start()
  t2.start()
  t3.start()
  t4.start()