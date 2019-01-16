import serial
import io
import threading
import logging
import time
from queue import Queue

BAUDRATE = 115200
TIMEOUT = 0.3
DELIMITER = "\r\n"

writeLock = threading.Lock()
LOCK_TIMEOUT = 10 # SECONDS

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

        self.writeQueue = Queue()

        logger.debug("initialized SerialInterface on port " + serialPort)

        self.writeAcquireTries = 0

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
            self.writeQueue.put(message)
            return True
        else:  
            logger.error("Write Lock Timeout reached (for '{}')".format(message))
            self.writeAcquireTries +=1
            if self.writeAcquireTries >= 3: # FALLBACK MECHANISM TO PREVENT DEADLOCK
                logger.warn("Hard release write lock")
                writeLock.release()
            return False

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
            try:
                resp = self.interface.read()
                if resp != "" and len(resp) > 0:
                    text = resp[:-1] # Remove last linebreak
                    logger.debug("< '{}'".format(text))
                    self._startProcessingThread(text)
                time.sleep(0.1)
            except:
                logger.warn("Exception on reading serial input")

    def stop(self):
        self._stop_event.set()

    def _startProcessingThread(self, text):
        processor = threading.Thread(target=self.readListener, args=[text])
        processor.setDaemon(True)
        processor.start()
