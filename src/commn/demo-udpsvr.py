import socket
import time

IP = "255.255.255.255"
PORT = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

msg = b'A broadcast msg!'

while True:
  # block on port listening
  sock.sendto(msg, (IP, PORT))
  print("Msg sent")
  time.sleep(2)
