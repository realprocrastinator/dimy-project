import socket
import logging
import sys
import collections


class UDPManager(object):

  def __init__(self, name="", loglevel=logging.DEBUG, logfile=None):
    self.name = name
    # UDP settings
    self.sendsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    self.sendsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sendsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    self.recvsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    self.recvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.recvsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # global bessage sequence counter
    self.seqnum = 0
    # global sequence number records, only maintain two records
    self.seqnum_recs = collections.defaultdict(list)

    # logger
    logging.basicConfig(filename=logfile, filemode="a", \
        format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
    self.logger = logging.getLogger("UDPManager-" + self.name)
    shdlr = logging.StreamHandler(sys.stdout)
    shdlr.setLevel(logging.DEBUG)
    if (not self.logger.handlers):
      self.logger.addHandler(shdlr)
    self.logger.setLevel(loglevel)

  def send_msg(self, ip, port, msg_bytes):
    try:
      nbytes = self.sendsock.sendto(msg_bytes, (ip, port))
      self.logger.debug(f"Sent {nbytes} bytes to address({ip}, {port}): 0x{msg_bytes.hex()}")
    except OSError:
      self.logger.error("Failed to send message")

  def recv_msg(self, bufsz=1024):
    # block
    msg_bytes, (ip, port) = self.recvsock.recvfrom(bufsz)
    self.logger.debug(f"Receiving msg from address({ip}, {port}): 0x{msg_bytes.hex()}")

    return msg_bytes

  def bind_address(self, ip, port):
    self.recvsock.bind((ip, port))
