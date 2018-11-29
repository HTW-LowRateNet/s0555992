# SEE
# https://pyserial.readthedocs.io/en/latest/shortintro.html

import serial
import io
import sys
import threading
import random
import time

readLock = threading.Lock()

coordinatorFound = 0
isCoordinator = 0

ser = serial.Serial(
    port=sys.argv[1],
    baudrate=115200,
    timeout=0.3
)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

if(not ser.isOpen()):
    ser.open()

commands = [
	'AT+RST',
	'AT+CFG=433000000,20,9,10,1,1,0,0,0,0,3000,8,4',
	'AT+ADDR=' + "%04x" % random.randint(0x0001, 0x000F), # RANDOM ADRESS
	'AT+SAVE'
]

def read_input():
    readLock.acquire()
    resp = sio.readline()
    while resp != "":
       process_message(resp[:-1]) # Remove last linebreak
       resp = sio.readline()
    readLock.release()

def send_command(command):
    print(command)
    sio.write(command + "\r\n")
    sio.flush()
    read_input()
    

def send_message(receiver, message):
    send_command('AT+DEST=' + receiver)
    send_command('AT+SEND=' + str(len(message)))
    send_command(message)

def process_message(message):
    print('<< ' + message)
    parts = message.split(',')
    if len(parts) < 3:
        return
    sender = parts[1]
    cont = parts[3]

    global coordinatorFound
    if not coordinatorFound and sender.startswith("0000") and cont.startswith("ALIV"):
        # COORDINATOR FOUND 
        coordLock.acquire()
        coordinatorFound = 1
        global isCoordinator
        isCoordinator = 0
        print("Got coord")
        coordLock.release()


for cmd in commands:
	send_command(cmd)


class ReadThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._is_running = True
    def run(self):
        while self._is_running:
            read_input()
            time.sleep(0.1)
    def stop(self):
        self._is_running = False

class CoordAlivThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._is_running = True
    def run(self):
        while self._is_running:
            send_message('FFFF', 'ALIV')
            time.sleep(6)
    def stop(self):
        self._is_running = False

readThread = ReadThread()
readThread.start()

coordLock = threading.Lock()

coordThread = CoordAlivThread()

for x in range(1, 7):
    coordLock.acquire()
    if not coordinatorFound:
        print("no coordinator. request no " + str(x))
        coordLock.release()
        send_message('FFFF', 'KDIS')
    else:
        print
        coordLock.release()
        break
    time.sleep(3)

coordLock.acquire()
if not coordinatorFound:
    print("being coordinator now")
    send_command('AT+ADDR=0000')
    isCoordinator = 1
    coordinatorFound = 1
    coordThread.start()
coordLock.release()

print("after coord disc")

def doExit():
    print("do Exit")
    readThread.stop()
    coordThread.stop()
    exit()

while 1:
    input_val = input("")
    print(input_val)
    if input_val == 'exit':
        doExit()
    else:
        sio.write(input_val + '\r\n')
        sio.flush()
