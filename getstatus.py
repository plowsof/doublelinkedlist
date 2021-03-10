import socket
import time
UDP_IP = "127.0.0.1"
UDP_PORT = 28910
UDP_RCON_PASSWORD = "$rcon_password"
print("UDP target IP:", UDP_IP)
print("UDP target port:", UDP_PORT)


def udp_send(MESSAGE):
	global UDP_PORT,UDP_IP,UDP_RCON_PASSWORD
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
	for x in MESSAGE:
		pak = f"\xFF\xFF\xFF\xFFrcon {UDP_RCON_PASSWORD} {x}"
		sock.sendto(bytes(pak, "latin-1"), (UDP_IP, UDP_PORT))
		data = sock.recv(1400)
		resp = data.decode('latin-1')
		return resp.split("\n")[1]
