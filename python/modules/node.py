import modules.serial_interface as serial
import threading
import time
import random
import modules.message as message
import logging

logger = logging.getLogger(__name__)

SLEEP_BETWEEN_ADDR = 10 #SECONDS

def getRandomAddress():
    # SET RANDOM ADDRESS
    return random.randint(0x0011, 0x00FF)

class Node:

    def __init__(self, address = getRandomAddress()):
        self.messageIdCount = 0x0000
        self.setAddress(address, True)
        self.forwardedMessages = set()
        self.randomAddr = True

    def setAddress(self, address, parse=False):
        if parse:
            self.address = "%04X" % address
        else:
            self.address = address
        logger.info("Set address to " + self.address)
        serial.write("AT+ADDR=" + self.address)

    def onMessage(self, msg):
        logger.debug("Got message from '{}' [{}]: {}".format(msg.src, msg.code, msg.payload))

        if(msg.dest == self.address):
            self.onOwnMessage(msg)
        else:
            msgId = "{}-{}#{}".format(msg.src, msg.dest, msg.id)
            if(msgId not in self.forwardedMessages):
                msg.hops += 1
                if(msg.hops >= msg.ttl):
                    logger.debug("Message reached it's end of life")
                else:
                    logger.debug("Forwarding ...")
                    self.sendMessage(msg)
                    self.forwardedMessages.add(msgId)
            else:
                logger.debug("Already forwarded message")

    def onOwnMessage(self, msg):
        logger.info("Got message from '{}': {}".format(msg.src, msg.payload))
        if(msg.src=="0000" and msg.code==message.Code.ADDRESS):
            if self.randomAddr:
                self.setAddress(msg.payload)
                self.sendMessage(message.addressAcknowledge(self.address))
                self.randomAddr = False

    def sendMessage(self, msg):
        msg.id="%04x" % self.messageIdCount
        messageString = msg.toString()
        logger.debug("Sending message '{}'".format(messageString))
        serial.write('AT+SEND=' + str(len(messageString)))
        serial.write(messageString)
        self.messageIdCount += 1

    def requestAddress(self):
        addr = threading.Thread(target=self._requestAddress)
        addr.start()

    def _requestAddress(self):
        while self.randomAddr:
            self.sendMessage(message.addressRequest(self.address))
            time.sleep(SLEEP_BETWEEN_ADDR)

