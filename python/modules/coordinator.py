from modules.node import Node
from threading import Thread
import time

class Coordinator(Node):

    def __init__(self):
        Node.__init__(self, "0000")
        self.startKeepAlive()

    def startKeepAlive(self):
        self.keepAlive = CoordAlivThread(self)
        self.keepAlive.start()

    def stopKeepAlive(self):
        print("stopping Coordinator keepalive")
        self.keepAlive.stop()

    def onMessage(self, sender, message):
        print("Coordinator handling message") 
        # TODO CHECK WHETHER COORDINATOR WAS REQUESTED
        super(Coordinator, self).onMessage(sender, message)

class CoordAlivThread (Thread):
    def __init__(self, coordinator):
        Thread.__init__(self)
        self._is_running = True
        self.coordinator = coordinator
    def run(self):
        while self._is_running:
            self.coordinator.sendMessage("FFFF", "ALIV")
            time.sleep(6)
    def stop(self):
        self._is_running = False
