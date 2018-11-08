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

ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=115200,
    timeout=0.1
)
sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

if(not ser.isOpen()):
    ser.open()

start_new_thread(read_input, ())

while 1:
    input_val = input("")
    if input_val == 'exit':
        ser.close()
        exit()
    else:
        sio.write(input_val + '\r\n')
        sio.flush()
