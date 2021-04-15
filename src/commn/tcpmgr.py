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

# global config
# TODO(Jiawei): move it to config, don't hard code here
URL = "http://ec2-3-26-37-172.ap-southeast-2.compute.amazonaws.com:9000/comp4337/{0}"
suffix = {"upload": "cbf/upload", "query": "qbf/query"}


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
  except KeyError as e:
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
        log(f"Result: {resp}", msg)
      else:
        log("Enpty status.")
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
        log(f"Result: {res}", msg)
      else:
        log("Enpty status.")
    else:
      # error caused by http request, maybe network failure or server down
      log(f"HTTP request failed with status code {r.status_code}")

  except Exception as e:
    log(e)

  return res, msg


if __name__ == "__main__":
  # unit test API
  URL = "http://ec2-3-26-37-172.ap-southeast-2.compute.amazonaws.com:9000/comp4337/{0}"

  suffix = {"upload": "cbf/upload", "query": "qbf/query"}

  bfmgr = bfmng.BloomFilterManager()

  for _ in range(bfmgr.max_poolsz):
    bfmgr.update_dbfpool_atomic()

  bfmgr.cluster_dbf(bfmgr.max_poolsz, "QBF")

  bfmgr.cluster_dbf(bfmgr.max_poolsz, "CBF")

  # Valid data but less than 100KB
  res = upload_cbf(URL.format(suffix["upload"]), {"CBF": "A"})
  assert (res == True)
  print("Test CBF with data < 100KB\n")

  # Invalid data format
  res = upload_cbf(URL.format(suffix["upload"]), {"HAHAHA"})
  assert (res == False)
  print("Test invalid data format passed\n")

  # Wrong url
  res = upload_cbf(URL[:-10], {"HAHAHA"})
  assert (res == False)
  print("Test Wrong url passed\n")

  # Valid cbf with no data
  data = {"CBF": bfmgr.dump_bf("CBF")}
  res = upload_cbf(URL.format(suffix["upload"]), data)
  assert (res == True)
  print("Test null CBF passed\n")

  # inseret into DBF and rebuild cbf then upload
  bfmgr.insert_to_dbf("Hello World")
  bfmgr.insert_to_dbf("Hello")
  bfmgr.insert_to_dbf("World")

  bfmgr.cluster_dbf(bfmgr.max_poolsz, "CBF")

  # Valid cbf with data
  data = {"CBF": bfmgr.dump_bf("CBF")}
  res = upload_cbf(URL.format(suffix["upload"]), data)
  assert (res == True)
  print("Test upload cbf with data passed\n")

  bfmgr.cluster_dbf(bfmgr.max_poolsz, "QBF")
  data = {"QBF": bfmgr.dump_bf("QBF")}
  # query match
  res, msg = query_qbf(URL.format(suffix["query"]), data)
  assert (res == "Match")
  assert (
      msg ==
      "You are potentially at risk. Please consult a health official, self-isolate and do a COVID-19 test at your earliest."
  )
  print("Test query match passed\n")

  # query unmatch
  data = {"QBF": bfmgr.dump_bf("DBF", 1)}
  res, msg = query_qbf(URL.format(suffix["query"]), data)
  assert (res == "No Match")
  assert (msg == "You are safe.")
  print("Test unmatch QBF passed\n")

  # # invalid query
  res, msg = query_qbf(URL.format(suffix["query"]), {})
  assert (res == "Failed")
  assert (msg == "please check your QBF")
  print("Test invalid QBF passed\n")
