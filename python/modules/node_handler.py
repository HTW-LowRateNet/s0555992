from modules.node import Node
from modules.coordinator import Coordinator
import threading
import time
import modules.serial_interface as serial
import random

TRIES_TO_DISCOVER = 6
SLEEP_BETWEEN_DISCOVER = 6 # SECONDS

class NodeHandler:

    def __init__(self):
        self.coordLock = threading.Lock()
        self.hasCoordinator = False
        commands = [
            'AT+RST',
            'AT+CFG=433000000,20,9,10,1,1,0,0,0,0,3000,8,4',
            'AT+SAVE'
        ]
        # GENERAL MODULE CONFIGURATION
        print("Configuring module")
        for cmd in commands:
            serial.write(cmd)

        # SET RANDOM ADDRESS
        address = "%04x" % random.randint(0x0001, 0x000F)
        print("Set random address " + address)
        # NODE
        self.node = Node(address)

    def onSerialInput(self, text):
        print('<< ' + text)
        parts = text.split(',')
        if len(parts) < 3:
            return
        sender = parts[1]
        content = parts[3]

        if not self.hasCoordinator and sender.startswith("0000") and content.startswith("ALIV"):
            # COORDINATOR FOUND 
            self.coordLock.acquire()
            self.hasCoordinator = 1
            print("Got coord")
            self.coordLock.release()
        else:
            # OTHER MESSAGE: DISPATCH TO NODE
            self.node.onMessage(sender, content)
    
    def discoverCoordinator(self):
        for x in range(0, TRIES_TO_DISCOVER):
            self.coordLock.acquire()
            if not self.hasCoordinator:
                print("no coordinator. request no " + str(x + 1))
                self.coordLock.release()
                self.node.sendMessage("FFFF", "KDIS")
            else:
                self.coordLock.release()
                break
            time.sleep(SLEEP_BETWEEN_DISCOVER)

        self.coordLock.acquire()
        if not self.hasCoordinator:
            print("being coordinator now")
            self.makeCoordinator()
        self.coordLock.release()

    def makeCoordinator(self):
        self.node = Coordinator()

    def start(self):
        print("Starting node handler")
        self.readThread = ReadThread(self)
        self.readThread.start()
        self.discoverCoordinator()

    def stop(self): 
        print("Shutting down node handler...")
        self.readThread.stop()
        if isinstance(self.node, Coordinator):
            self.node.stopKeepAlive()


class ReadThread (threading.Thread):
    def __init__(self, handler):
        threading.Thread.__init__(self)
        self._is_running = True
        self.handler = handler
    def run(self):
        while self._is_running:
            serial.read(self.handler.onSerialInput)
            time.sleep(0.1)
    def stop(self):
        self._is_running = False
