from modules.node import Node
import threading
import time
import modules.message as message

SLEEP_BETWEEN_HEARTBEAT = 10 # SECONDS

class Coordinator(Node):

    def __init__(self):
        Node.__init__(self)
        self.setAddress("0000")
        self.lastheartbeat = 0.0
        self.startKeepAlive()

    def startKeepAlive(self):
        self.keepAlive = CoordAlivThread(self)
        self.keepAlive.start()

    def stopKeepAlive(self):
        print("stopping Coordinator keepalive")
        self.keepAlive.stop()

    def onMessage(self, msg):
        print("Coordinator handling message") 

        actions = {
            message.Code.COORD_DISCOVERY : self.handleDiscovery,
            message.Code.ADDRESS : self.handleAddress
        }
        
        if(msg.code in actions):
            actions[msg.code]()
            return
        else:
            print("Unsupported message code " + str(msg.code))
        

        if(msg.dest != "0000"):
            # NO COORDINATOR MESSAGE
            super(Coordinator, self).onMessage(msg)
            return
        
    def handleDiscovery(self):
        print("Aliv requested")
        self._sendHeartbeat()
    
    def handleAddress(self, msg):
        print("Address requested")
        pass
        
    def _sendHeartbeat(self):
        self.sendMessage(message.coordinatorHeartbeat())
        self.lastheartbeat = time.time()

class CoordAlivThread (threading.Thread):
    def __init__(self, coordinator):
        threading.Thread.__init__(self)
        self._is_running = True
        self.coordinator = coordinator
    def run(self):
        while self._is_running:
            delta = time.time() - self.coordinator.lastheartbeat
            if(delta >= SLEEP_BETWEEN_HEARTBEAT - 1): # -1 to compensate serial timeout
                self.coordinator._sendHeartbeat()
    def stop(self):
        self._is_running = False
