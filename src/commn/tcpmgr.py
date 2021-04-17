import sys
import requests
import json
import sys
import os
from pathlib import Path  # if you haven't already done so

# Add toor dir of the src tree to the syspath, so that we can use absolute import
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

import bfmng


# log can be any printing function
# status should a dict type
def parse_response(status, log):
  res, msg = None, None
  try:
    if "status" not in status.keys():
      # success / fail
      res, msg = status["result"], status["message"]
    else:
      # error occured
      res, msg = status["status"], status["error"]
  except KeyError:
    log("Entry not found! Might because API changed?")

  return res, msg


def upload_cbf(url, data, log_func=None):
  log = log_func if log_func else print

  try:
    r = requests.post(url, json=data)
    if (r.ok):
      status = json.loads(r.content.decode("utf-8"))

      # parse response to get the internal result
      if (status):
        resp, msg = parse_response(status, log_func)
        log(f"Result from server: {resp}, {msg}")
      else:
        log("Empty status.")
      res = (resp == "Success")
    else:
      # error caused by http request, maybe network failure or server down
      res = False
      log(f"HTTP request failed with status code {r.status_code}")
  except Exception as e:
    log(e)
    res = False
  return res


# return None on error, result + msg on success
def query_qbf(url, data, log_func=None):
  log = log_func if log_func else print

  res = None
  msg = None

  try:
    r = requests.post(url, json=data)
    if (r.ok):
      status = json.loads(r.content.decode("utf-8"))

      # parse response to get the internal result
      if (status):
        res, msg = parse_response(status, log_func)
        log(f"Result from server: {res}, {msg}")
      else:
        log("Empty status.")
    else:
      # error caused by http request, maybe network failure or server down
      log(f"HTTP request failed with status code {r.status_code}")

  except Exception as e:
    log(e)

  return res, msg
