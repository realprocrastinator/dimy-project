import json
import logging

DEFAULT = {
    # UDP config
    "UDP_RCV_IP": "",
    "UDP_RCV_PORT": 8080,
    "UDP_SND_IP": "255.255.255.255",
    "UDP_SND_PORT": 8080,

    # BloomFilter config
    "BF_BITS": 800000,
    "BF_NHASHFUNS": 3,
    "BF_ARRSZ_BITS": 8,

    # BloomFilter Manager config
    "BFMGR_INIT_NDBFS": 6,
    "BFMGR_MAX_DBF_POOLSZ": 6,
    "BFMGR_LOGLEVEL": logging.DEBUG,

    # BackGround Worker config
    "BGWRK_LOGLEVEL": logging.DEBUG,

    # Background Task config
    "BG_GEN_EphID_SECS": 12,
    "BG_SHARE_EphID_SECS": 1,
    "BG_RECV_CHECK_SECS": 7,
    "BG_DBFPOOL_UPDATE_SECS": 30,
    "BG_QBF_GEN_SECS": 10,

    # Server config
    "URL_TEMPLATE": "http://ec2-3-26-37-172.ap-southeast-2.compute.amazonaws.com:9000/comp4337/{0}",
    "URL_SUFFIX": {
        "UPLOAD": "cbf/upload",
        "QUERY": "qbf/query"
    },

    # Debugging config
    "STDOUT_LOGLEVEL": logging.INFO,
    "ALL_LOG_LEVEL": logging.DEBUG,
    "DEBUG_MODE": True,
    "ALL_LOG_FILE": "log.txt",

    # MISC config
    # Shamir Algo config
    "NUM_SECRET_PARTS": 6,
    "NUM_THRESHOLD": 3
}


# load the user given configurations
def load_grp03_global_config(filepath=None):
  if (not filepath):
    print("Using default configuration")
    return DEFAULT

  # try open the file, let it fail if not exist
  with open(filepath, "r") as f:
    config = json.load(f.read())

  # verify important keys
  for k in DEFAULT.keys():
    if (k not in config):
      raise ValueError(f"Missing configuration entry key : {k}")

  print("Using custom configuration")
  return config