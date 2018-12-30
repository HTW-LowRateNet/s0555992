from modules.node import Node
import threading
import time
import modules.message as message
import logging

logger = logging.getLogger(__name__)

SLEEP_BETWEEN_HEARTBEAT = 20 # SECONDS

class Coordinator(Node):

    def __init__(self):
        Node.__init__(self)
        self.setAddress(0xFFFF, True)
        self.addressCount=0x0010 #0010 - FFFE
        self.lastheartbeat = 0.0
        self.startKeepAlive()

    def startKeepAlive(self):
        self.keepAlive = CoordAlivThread(self)
        self.keepAlive.start()

    def stopKeepAlive(self):
        logger.debug("stopping Coordinator keepalive")
        self.keepAlive.stop()
        self.keepAlive.join()

    def onMessage(self, msg):
        logger.debug("Coordinator handling message") 

        actions = {
            message.Code.COORD_DISCOVERY : self.handleDiscovery,
            message.Code.ADDRESS : self.handleAddress
        }
        
        if(msg.code in actions):
            actions[msg.code](msg)
            return
        else:
            logger.debug("Unsupported message code " + str(msg.code))

        if(msg.dest != "0000"):
            # NO COORDINATOR MESSAGE
            super(Coordinator, self).onMessage(msg)
            return
        
    def handleDiscovery(self, msg):
        logger.debug("Aliv requested")
        self._sendHeartbeat()
    
    def handleAddress(self, msg):
        logger.debug("Address requested")
        self.sendMessage(message.addressResponse(msg.src, "%04x" % self.addressCount))
        self.addressCount = (self.addressCount + 1)

    def _sendHeartbeat(self):
        self.sendMessage(message.coordinatorHeartbeat())
        self.lastheartbeat = time.time()

class CoordAlivThread (threading.Thread):
    def __init__(self, coordinator):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self.coordinator = coordinator
    def run(self):
        while not self._stop_event.is_set():
            delta = time.time() - self.coordinator.lastheartbeat
            if(delta >= SLEEP_BETWEEN_HEARTBEAT - 1): # -1 to compensate serial timeout
                self.coordinator._sendHeartbeat()
    def stop(self):
        self._stop_event.set()
