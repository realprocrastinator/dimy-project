import sys
import logging
import sys
import signal
import time
from pathlib import Path  # if you haven't already done so

# Add toor dir of the src tree to the syspath, so that we can use absolute import
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

from bgwork import job


class BackgroundManager(object):
  """
  This is a back ground worker class which can be assigned with multiple
  periodic tasks.
  """

  def __init__(self, loglevel=logging.DEBUG, logfile=None):
    self.jobs = []

    # configure logger
    logging.basicConfig(filename=logfile, filemode="a", \
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
    self.logger = logging.getLogger("BGWorker")
    shdlr = logging.StreamHandler(sys.stdout)
    shdlr.setLevel(logging.INFO)
    shdlr.createLock()
    self.shdlr = shdlr
    if (not self.logger.handlers):
      self.logger.addHandler(shdlr)
    self.logger.setLevel(loglevel)

  # This function is only used internally
  def add_job(self, jobname, interval, isdaemon, handler, *args, **kargs):
    j = job.Job(jobname, interval, handler, isdaemon, *args, **kargs)
    self.jobs.append(j)

  # Lets use decorator for creating a job to make it generic
  def myjob(self, jobname, interval, isdaemon):

    def wrapper(f, *args, **kargs):
      self.add_job(jobname, interval, isdaemon, f, *args, **kargs)
      # return f

    return wrapper

  # This function should be called internally
  def _start_jobs(self):
    for j in self.jobs:
      self.logger.debug(f"Starting job {j.name}")
      j.start()

  def start_all(self):
    self.logger.debug("Starting background worker...")
    self._start_jobs()

  def start_job(self, jobname, if_restart=False):
    self.logger.debug(f"Starting job {jobname}")
    for j in self.jobs:
      if (j.name == jobname):
        j.start()

  def _stop_jobs(self):
    for j in self.jobs:
      self.logger.debug(f"Stopping job {j.name}")
      j.stop()

  def stop_all(self):
    self.logger.debug(f"Stopping background worker...")
    self._stop_jobs()

  def stop_job(self, jobname):
    self.logger.debug(f"Stopping job {jobname}")
    for j in self.jobs:
      if j.name == jobname:
        j.stop()
        self.jobs.remove(j)