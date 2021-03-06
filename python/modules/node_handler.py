from modules.node import Node
from modules.coordinator import Coordinator
import modules.message as message
import modules.serial_interface as serial
import threading
import time
import logging

# NUMBER OF TRIES TO FIND COORDINATOR
TRIES_TO_DISCOVER = 3

# TIME BETWEEN DISCOVER MESSAGES
SLEEP_BETWEEN_DISCOVER = 15 # SECONDS

# TIME TO WAIT BETWEEN COORDINATOR'S ALIV BEFORE BECOMING COORDINATOR
TIMEOUT_FOR_COORDINATOR_ALIVE = 90

logger = logging.getLogger(__name__)

class NodeHandler(threading.Thread):

    def __init__(self, serial):
        '''
        Constructor

        Configures module by calling AT commands
        '''
        logger.info("##### INITIALIZING #####")
        threading.Thread.__init__(self)
        self.serial = serial
        self._stop_event = threading.Event()
        self.coordLock = threading.Lock()
        self.hasCoordinator = False
        self.lastCoordinatorAlive = 0
        commands = [
            'AT+CFG=433000000,20,9,10,1,1,0,0,0,0,3000,8,4',
            'AT+DEST=FFFF', # BROADCAST EVERYTHING
            'AT+SAVE'
        ]

        self.serial.start(self.onSerialInput)
        # GENERAL MODULE CONFIGURATION
        logger.debug("Configuring module")
        for cmd in commands:
            if not self.serial.write(cmd):
                raise RuntimeError("Configuration failed")
        
        # NODE
        self.node = Node(self)

    def onSerialInput(self, text):
        '''
        callback method for input on serial interface
        '''
        if text == "AT,OK" or text == "AT,SENDED" or text.startswith("ERR"):
            self._atResponse(text)         
            return

        if text.startswith("LR"):
            try:
                msg = message.parseMessage(text)
                self._onMessage(msg)
            except:
                logger.warn("Invalid message: " + text)
                return

    def _atResponse(self, text):
        cmd = self.serial.writeQueue.get(False)
        logger.debug("! {} ({})".format(text,cmd))
        serial.writeLock.release()

    def _onMessage(self, msg):
        actions = {
            message.Code.COORD_ALIVE : self._onCoordinatorAlive,
            message.Code.NETWORK_RESET : self._onResetMessage
        }
                
        logger.debug("Message: " + msg.toString())
        
        if(msg.code in actions):
            actions[msg.code](msg)
        else:
            # OTHER MESSAGE: DISPATCH TO NODE
            self.node.onMessage(msg)

    def isCoordinator(self):
        '''
        returns boolean whether running in coordinator mode
        '''
        return isinstance(self.node, Coordinator)

    def shutdown(self): 
        '''
        shuts down all threads
        '''
        logger.info("Shutting down node handler...")
        self._stop_event.set()
        self.serial.stop()

        if self.isCoordinator():
            self.node.stopKeepAlive()

    def sendMessage(self, dest, text):
        '''
        delegate a text message to node for chatting
        '''
        self.node.sendMessage(message.message(self.node.address, dest, text))

    def _onResetMessage(self, msg):
        if msg.src == "0000":
            logger.warn("Network reset from coordinator!")
            self._reset()
        else:
            logger.debug("Network reset from other node ignored")

    def _reset(self):
            self.node=Node(self)
            self._resetCoordinator()

    def _resetCoordinator(self):
        '''
        reset found coordinator and restart discovery
        '''
        self.coordLock.acquire()
        self.hasCoordinator = False
        self.coordLock.release()
        self.discoverCoordinator()


    def _onCoordinatorAlive(self, msg):
        '''
        handle ALIVE Message from coordinator
        '''
        self.lastCoordinatorAlive = time.time()
        logger.debug("Coordinator alive")

        if self.isCoordinator():
            if msg.id in self.node.heartbeats:
                logger.debug("Got own alive back")
                return
            logger.warn("Got alive from other coordinator")
            self.node.sendMessage(message.networkReset(self.node.address))
            logger.info("Handle network reset!")
            self._reset()

        elif not self.hasCoordinator:
            logger.info("Coordinator present")
            self.coordLock.acquire()
            self.hasCoordinator = True
            self.coordLock.release()
            timeout = threading.Thread(target=self._coordinatorTimeout)
            timeout.setDaemon(True)
            timeout.start()
            self.node.requestAddress()

        else:
            self.node.forwardMessage(msg)

    def run(self):
        self.discoverCoordinator()

    def discoverCoordinator(self):
        '''
        try discovering a coordinator in network
        if discovery fails, become coordinator
        '''
        logger.info("##### DISCOVERING #####")
        for x in range(0, TRIES_TO_DISCOVER):
            if(self._stop_event.isSet()):
                return
            self.coordLock.acquire()
            if not self.hasCoordinator:
                logger.info("no coordinator. request no " + str(x + 1))
                self.coordLock.release()
                self.node.sendMessage(message.discoverCoordinator(self.node.address))
            else:
                self.coordLock.release()
                break
            self._stop_event.wait(SLEEP_BETWEEN_DISCOVER)

        self.coordLock.acquire()
        if not self.hasCoordinator:
            self._makeCoordinator()
        self.coordLock.release()

    def _makeCoordinator(self):
        '''
        Start coordinator mode
        '''
        self.node = Coordinator(self)
        self.hasCoordinator = True
        
        logger.info("##### BEING COORDINATOR #####")

    def _coordinatorTimeout(self):
        '''
        Method for timeout check of coordinator's heartbeat

        supposed to run in thread
        '''
        while self.hasCoordinator and not self.isCoordinator():
            delta = time.time() - self.lastCoordinatorAlive + 1 # compensation for timeouts
            if(delta >= TIMEOUT_FOR_COORDINATOR_ALIVE):
                logger.debug("!!! Coordinator timed out")
                if not self.isCoordinator():
                    self._reset()