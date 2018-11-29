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
        print("stopping keepalive")
        self.keepAlive.stop()


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
