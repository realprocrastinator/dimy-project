import sys
import logging

# costum modules
import commn
from bgwork.bgmgr import BackgroundManager

####################
# Background tasks #
####################


# background task for periodically generating the EphID and broadcast it
def bg_gen_and_bdcast_EphID(idmngr, ip, port, share_interval):

  ephid = idmngr.gen_EphID()
  if (not ephid):
    idmngr.logger.error("Failed to generat EphID")

  # simulate send one share every 2s
  idmngr.share_EphID(ephid, share_interval, ip, port)


# background task for periodically checking whether can reconstruct EphID and insert EncntID to DBF
def bg_receive_and_try_reconstruct_EcntID(idmngr, bfmgr, ip, port, threshold):
  encntid = idmngr.wait_for_secret(ip, port, threshold, filter_self=False)
  
  if (encntid):
    # insert to the DBF
    bfmgr.logger.info("\n------------------> Segment 6 & 7 <------------------"
                      "\nInserting a new EncntID to the DBF (murmur3 hashing with 3 hashes)")
    bfmgr.insert_to_dbf(encntid)


# background task for periodically updating the DBF pool, remove the oldest one and add the new one
def bg_update_dbf_pool(bfmgr):
  bfmgr.logger.info("\n--------------------> Updating DBF Pool <--------------"
                    "\nUpdating the DBF pool...Removing the oldest DBF and add a new DBF\n")
  bfmgr.update_dbfpool_atomic()


# background task for periodically querying the server with QBF
def bg_qbf_woker_combine_and_query(bfmgr, url):
  qbf = bfmgr.cluster_dbf(bfmgr.max_poolsz, type_name="QBF")
  if (qbf):

    bfmgr.logger.info("\n------------------> Segment 8 & 9 <------------------"
                     f"\nQuerying the sever with QBF ID: {qbf.id}\n")

    res, msg = commn.query_qbf(url,\
                               {"QBF" : bfmgr.dump_bf("QBF", bf = qbf)})

    bfmgr.logger.info("\n============================="
                     f"\nGot the result from server: {res}, {msg}"
                      "\n=============================\n")

  else:
    bfmgr.logger.info("\n------------------> Segment 8 & 9 <------------------"
                      "\nQBF not ready, may be pool is not full yet?\n")


############################
# Background tasks helpers #
############################


# add background job wrapper
def bg_task_install(bgmgr, task_name, interval, task_hdlr, *args, **kargs):
  bgmgr.add_job(task_name, interval, True, task_hdlr, *args, **kargs)


########################
# Non-Background tasks #
########################


# user controlled combine and upload CBF to the server
def nbg_cbf_combine_and_upload(mgr, url):
  # updating the DBF pool
  cbf = mgr.cluster_dbf(mgr.max_poolsz, type_name="CBF")

  if (cbf):
    # TODO(Jiawei): make url configurable
    res = commn.upload_cbf(url,\
                               {"CBF" : mgr.dump_bf("CBF", bf = cbf)}, log_func=mgr.logger.debug)

    mgr.logger.info("\n============================="
                   f"\nGot the result from server: {'Success' if res else 'Failed'}"
                    "\n=============================\n")

  else:
    mgr.logger.info("CBF not ready, may be pool is not full yet?")

  mgr.logger.info("\n")