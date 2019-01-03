import serial
import io
import threading
import logging

BAUDRATE = 115200
TIMEOUT = 0.3
DELIMITER = "\r\n"

readLock = threading.Lock()
writeLock = threading.Lock()

logger = logging.getLogger(__name__)

def initIOWrapper(serialPort):

    global ser
    ser = serial.Serial(
        port=serialPort,
        baudrate=BAUDRATE,
        timeout=TIMEOUT
    )

    if(not ser.isOpen()):
        ser.open()
    
    global sio
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

    logger.debug("initialized IOWrapper for Serial port " + serialPort)

def read(callback):
    '''
    reads input from serial and passes content to callback method
    '''
    resp = ""
    with readLock:
        resp = sio.readline()
    if resp != "":
        text = resp[:-1] # Remove last linebreak
        callback(text)
        read(callback)

def toSysout(message):
    logger.debug("< serial '{}'".format(message))

def write_cb(message, callback):
    with writeLock:
        logger.debug("> '{}'".format(message))
        sio.write(message + DELIMITER)
        sio.flush()
        read(callback)

def write(message):
    write_cb(message, toSysout)
