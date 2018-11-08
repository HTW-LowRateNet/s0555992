# SEE
# https://pyserial.readthedocs.io/en/latest/shortintro.html

import serial
import io
from _thread import start_new_thread

def read_input():
    while 1:
        read = sio.readline()
        if read != "":
            print(">> " + read[:-1]) # Remove last linebreak

def send_command(command):
    print(command)
    sio.write(command + '\r\n')
    sio.flush()
    resp = sio.readline()
    while resp != "":
       print('>> ' + resp[:-1])
       resp = sio.readline()

ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=115200,
    timeout=0.3
)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

if(not ser.isOpen()):
    ser.open()

commands = [
	'AT+RST',
	'AT+CFG=433000000,20,6,10,1,1,0,0,0,0,3000,8,4',
	'AT+ADDR=2121',
	'AT+SAVE'
]

for cmd in commands:
	send_command(cmd)

start_new_thread(read_input, ())

while 1:
    input_val = input("")
    if input_val == 'exit':
        ser.close()
        exit()
    else:
        sio.write(input_val + '\r\n')
        sio.flush()
