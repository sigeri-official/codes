import socket
from pynput.keyboard import Controller, Key

keyboard = Controller()

def press(key):
    keyboard.press(key)
    keyboard.release(key)

HOST = ""
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("Várakozás kapcsolatra...")
conn, addr = server.accept()
print(f"Kapcsolódva: {addr}")

while True:
    data = conn.recv(1024).decode()
    if not data:
        break
    press(data)

conn.close()
server.close()
