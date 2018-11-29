import serial
import io
import threading

BAUDRATE = 115200
TIMEOUT = 0.3
DELIMITER = "\r\n"

readLock = threading.Lock()

def initIOWrapper(serialPort):

    ser = serial.Serial(
        port=serialPort,
        baudrate=BAUDRATE,
        timeout=TIMEOUT
    )

    if(not ser.isOpen()):
        ser.open()
    
    global sio
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

    print("initialized IOWrapper for Serial port " + serialPort)

def read(callback):
    readLock.acquire()
    resp = sio.readline()
    while resp != "":
        text = resp[:-1] # Remove last linebreak
        toSysout(text)
        callback(text)
        resp = sio.readline()
    readLock.release()

def toSysout(message):
    print("\t< serial '{}'".format(message))

def write_cb(message ,callback):
    print("\t> serial '{}'".format(message))
    sio.write(message + DELIMITER)
    sio.flush()
    read(callback)

def write(message):
    write_cb(message, toSysout)