from modules.node import Node
import threading
import time
import modules.message as message
import logging

logger = logging.getLogger(__name__)
SLEEP_BETWEEN_HEARTBEAT = 20 # SECONDS

class Coordinator(Node):

    def __init__(self, handler):
        Node.__init__(self, handler, 0x0000)
        #self.setAddress(0xFFFF, True)
        self.addressCount=0x1000 #0010 - FFFE
        self.lastheartbeattime = 0.0
        self.startKeepAlive()
        self.heartbeats = set()

    def startKeepAlive(self):
        self.keepAlive = CoordAlivThread(self)
        self.keepAlive.start()

    def stopKeepAlive(self):
        logger.debug("stopping Coordinator keepalive")
        self.keepAlive.stop()

    def onMessage(self, msg):
        logger.debug("Coordinator handling message") 

        actions = {
            message.Code.COORD_DISCOVERY : self.handleDiscovery,
            message.Code.ADDRESS : self.handleAddress,
            message.Code.ADDRESS_ACK : self.handleAddressAck
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
        addr = "%04x" % self.addressCount
        logger.info("Address requested from {} [sending {}]".format(msg.src, addr))
        self.sendMessage(message.addressResponse(msg.src, addr))
        
    def handleAddressAck(self, msg):
        logger.info("Got Address Acknowledge [from {}]".format(msg.src))
        self.addressCount = (self.addressCount + 1)

    def _sendHeartbeat(self):
        id = self.sendMessage(message.coordinatorHeartbeat())
        if id != -1:
            self.lastheartbeattime = time.time()
            self.heartbeats.add(id)

class CoordAlivThread (threading.Thread):
    def __init__(self, coordinator):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self.coordinator = coordinator
        self.setDaemon(True)
    def run(self):
        while not self._stop_event.is_set():
            delta = time.time() - self.coordinator.lastheartbeattime
            if(delta >= SLEEP_BETWEEN_HEARTBEAT - 1): # -1 to compensate serial timeout
                self.coordinator._sendHeartbeat()
    def stop(self):
        self._stop_event.set()
