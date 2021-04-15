import socket
import logging
import sys

# default configurations
# TODO(Jiawei): make it configurable
DEFAULTBDCST_IP = "255.255.255.255"
DEFAULTBDCST_PORT = 8080
DEFAULTLISTENT_IP = ""

class UDPManager(object):
    def __init__(self, name = "", loglevel = logging.DEBUG):
        self.name = name
        # UDP settings
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # logger
        self.logger = logging.getLogger("UDPManager-" + self.name)
        shdlr = logging.StreamHandler(sys.stdout)
        shdlr.setLevel(loglevel)
        formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
        shdlr.setFormatter(formatter)
        self.logger.addHandler(shdlr)
        self.logger.setLevel(loglevel)

    def send_msg(self, ip, port, msg_bytes):
        self.logger.debug(f"Sending msg to address({ip}, {port}): {msg_bytes.decode('utf-8')}")
        nbytes = self.sock.sendto(msg_bytes, (ip, port))
        self.logger.debug(f"Sent {nbytes}")

    def recv_msg(self, bufsz = 1024):
        # block
        msg_bytes, (ip, port) = self.sock.recvfrom(bufsz)
        self.logger.debug(f"Receiving msg from address({ip}, {port}): {msg_bytes.decode('utf-8')}")
        
        return msg_bytes
    
    def bind_address(self, ip, port):
        self.sock.bind((ip, port))


if __name__ == "__main__":
    import threading
    import time

    # A same socket can handle both send and receive
    cli = UDPManager("cli")
    cli.bind_address(DEFAULTLISTENT_IP, DEFAULTBDCST_PORT)
    
    def cli_tsk():
        while True:
            cli.send_msg(DEFAULTBDCST_IP, DEFAULTBDCST_PORT, b"Hello World")
            time.sleep(2)

    def svr_tsk():
        while True:
            cli.recv_msg()

    t1 = threading.Thread(name="cli", target = cli_tsk)
    t2 = threading.Thread(name="svr", target = svr_tsk)

    t3 = threading.Thread(name="cli", target = cli_tsk)
    t4 = threading.Thread(name="cli", target = cli_tsk)

    t1.start()
    t2.start()
    t3.start()
    t4.start()



