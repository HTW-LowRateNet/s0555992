import serial
import io
import threading
import logging
import time

BAUDRATE = 115200
TIMEOUT = 0.3
DELIMITER = "\r\n"

writeLock = threading.Lock()
LOCK_TIMEOUT = 5 # SECONDS

logger = logging.getLogger(__name__)

class SerialInterface:

    def __init__(self, serialPort):
        logger.info("Opening serial port {}".format(serialPort))
        ser = serial.Serial(
            port=serialPort,
            baudrate=BAUDRATE,
            timeout=TIMEOUT
        )

        if(not ser.isOpen()):
            ser.open()
        
        self.sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

        logger.debug("initialized SerialInterface on port " + serialPort)

    def read(self):
        '''
        reads input from serial
        '''
        return self.sio.readline()

    def write(self, message):
        if writeLock.acquire(True, LOCK_TIMEOUT):
            logger.debug("> '{}'".format(message))
            self.sio.write(message + DELIMITER)
            self.sio.flush()
        else:  
            logger.warn("Write Lock Timeout reached")

    def start(self, readListener):
        self.reading = ReadThread(self, readListener)
        self.reading.start()

    def stop(self):
        self.reading.stop()
        try: 
            self.reading.join()
        except KeyboardInterrupt:
            logger.warn("ReadThread interrupted on shutdown")

class ReadThread (threading.Thread):
    '''
    thread for reading serial input
    '''
    def __init__(self, interface, readListener):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self.interface = interface
        self.setDaemon(True)
        self.readListener = readListener

    def run(self):
        while not self._stop_event.is_set():
            resp = self.interface.read()
            if resp != "" and len(resp) > 0:
                text = resp[:-1] # Remove last linebreak
                self._startProcessingThread(text)
            time.sleep(0.1)

    def stop(self):
        self._stop_event.set()

    def _startProcessingThread(self, text):
        processor = threading.Thread(target=self.readListener, args=[text])
        processor.start()
