import socket

IP = ""
PORT = 8080

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

client.bind(("", 8080))

while (True):
  # block
  msg, addr = client.recvfrom(1024)
  print(f"Msg from {addr}: {msg}")
