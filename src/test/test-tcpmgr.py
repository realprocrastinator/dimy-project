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
from commn.tcpmgr import *

# global config
URL = "http://ec2-3-26-37-172.ap-southeast-2.compute.amazonaws.com:9000/comp4337/{0}"
suffix = {"upload": "cbf/upload", "query": "qbf/query"}

if __name__ == "__main__":
  # unit test API
  
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
  assert (msg == "You are potentially at risk. Please consult a health official, self-isolate and do a COVID-19 test at your earliest.")
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
