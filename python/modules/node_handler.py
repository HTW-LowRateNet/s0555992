from modules.node import Node
from modules.coordinator import Coordinator
import modules.message as message
import threading
import time
import modules.serial_interface as serial
import logging

# NUMBER OF TRIES TO FIND COORDINATOR
TRIES_TO_DISCOVER = 0

# TIME BETWEEN DISCOVER MESSAGES
SLEEP_BETWEEN_DISCOVER = 20 # SECONDS

# TIME TO WAIT BETWEEN COORDINATOR'S ALIV BEFORE BECOMING COORDINATOR
TIMEOUT_FOR_COORDINATOR_ALIVE = 100

logger = logging.getLogger(__name__)

class NodeHandler:

    def __init__(self):
        '''
        Constructor

        Configures module by calling AT commands
        '''
        self.coordLock = threading.Lock()
        self.hasCoordinator = False
        self.lastCoordinatorAlive = 0
        commands = [
            'AT+RST',
            'AT+CFG=433000000,20,9,10,1,1,0,0,0,0,3000,8,4',
            'AT+DEST=FFFF', # BROADCAST EVERYTHING
            'AT+SAVE'
        ]
        # GENERAL MODULE CONFIGURATION
        logger.debug("Configuring module")
        for cmd in commands:
            serial.write(cmd)
        
        # NODE
        self.node = Node()

    def onSerialInput(self, text):
        '''
        callback method for input on serial interface
        '''
        if(text.startswith("AT")):
            serial.toSysout(text)
            return
        try:
            msg = message.parseMessage(text)
        except:
            logger.warn("Invalid message: " + text)
            return

        
        actions = {
            message.Code.COORD_ALIVE : self._handleCoordinatorAlive,
            message.Code.NETWORK_RESET : self._reset
        }
        
        if(msg.code in actions):
            actions[msg.code]()
        else:
            # OTHER MESSAGE: DISPATCH TO NODE
            self.node.onMessage(msg)

    def start(self):
        '''
        Start the handler

        executes thread for reading serial interface and
        starts discovery process
        '''
        logger.debug("Starting node handler")
        self.readThread = ReadThread(self)
        self.readThread.start()
        self._discoverCoordinator()

    def isCoordinator(self):
        '''
        returns boolean whether running in coordinator mode
        '''
        return isinstance(self.node, Coordinator)

    def stop(self): 
        '''
        shuts down all threads
        '''
        logger.info("Shutting down node handler...")
        self.readThread.stop()
        self.readThread.join()
                
        if self.isCoordinator():
            self.node.stopKeepAlive()

    def _reset(self):
        logger.debug("Handle network reset!")
        self.node=Node()
        self._resetCoordinator()

    def _resetCoordinator(self):
        '''
        reset found coordinator and restart discovery
        '''
        self.coordLock.acquire()
        self.hasCoordinator = False
        self.coordLock.release()
        self._discoverCoordinator()


    def _handleCoordinatorAlive(self, msg):
        '''
        handle ALIVE Message from coordinator
        '''
        self.lastCoordinatorAlive = time.time()
        logger.debug("Coordinator alive")
        if not(self.hasCoordinator and self.isCoordinator):
            logger.debug("Coordinator remembered")
            self.coordLock.acquire()
            self.hasCoordinator = True
            self.coordLock.release()
            timeout = threading.Thread(target=self._coordinatorTimeout)
            timeout.start()
            self.node.requestAddress()

    def _discoverCoordinator(self):
        '''
        try discovering a coordinator in network
        if discovery fails, become coordinator
        '''
        for x in range(0, TRIES_TO_DISCOVER):
            self.coordLock.acquire()
            if not self.hasCoordinator:
                logger.debug("no coordinator. request no " + str(x + 1))
                self.coordLock.release()
                self.node.sendMessage(message.discoverCoordinator(self.node.address))
            else:
                self.coordLock.release()
                break
            time.sleep(SLEEP_BETWEEN_DISCOVER)

        self.coordLock.acquire()
        if not self.hasCoordinator:
            logger.info("being coordinator now")
            self._makeCoordinator()
        self.coordLock.release()

    def _makeCoordinator(self):
        '''
        Start coordinator mode
        '''
        self.node = Coordinator()
        self.hasCoordinator = True

    def _coordinatorTimeout(self):
        '''
        Method for timeout check of coordinator's heartbeat

        supposed to run in thread
        '''
        while self.hasCoordinator:
            delta = time.time() - self.lastCoordinatorAlive + 1 # compensation for timeouts
            if(delta >= TIMEOUT_FOR_COORDINATOR_ALIVE):
                logger.debug("!!! Coordinator timed out")
                self._resetCoordinator()


class ReadThread (threading.Thread):
    '''
    thread for reading serial input
    '''
    def __init__(self, handler):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self.handler = handler
    def run(self):
        while not self._stop_event.is_set():
            serial.read(self.handler.onSerialInput)
            time.sleep(0.1)
    def stop(self):
        self._stop_event.set()
