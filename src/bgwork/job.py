# Add toor dir of the src tree to the syspath, so that we can use absolute import
import sys
from pathlib import Path  # if you haven't already done so

file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

import threading
from bgwork.exceptions import NullHandlerError


#TODO(gjw): 1. replace print with log; 2. add lock mechanism
class Job(threading.Thread):
  """
  A generic Job class tends to be running in the background. The handler of each job
  will be involked after a timer which is set by the interval argument fires. 
  """

  def __init__(self, jobname, interval, handler, isdaemon, *args, **kargs):
    super().__init__(name=jobname, daemon=isdaemon)
    self._ifstop = threading.Event()
    self._interval = interval
    # self.lock = None # need a lock when accessing global data structures
    self._handler = handler
    self._args = args
    self._kargs = kargs

  def run(self):
    if not self._handler:
      print(f"ERROR: Handler not installed in Job {self.name}")
      raise NullHandlerError

    # stop only if we are signaled
    # wait until timeout to involke the handler using this conditional variable
    while not self._ifstop.wait(timeout=float(self._interval)):
      print(f"\n\nThe handler of job {self.name} is being involked.")
      self._handler(*self._args, **self._kargs)

    print(f"Job {self.name} stops running.")

  def stop(self):
    # terminate gracefully and clean up resources
    self._ifstop.set()
    print(f"Job {self.name} is going to terminate.")
    print("Cleaning up\n")

    # Don't create any Zommmmmbiesssss
    self.join()
