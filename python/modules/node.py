import threading
import time
import random
import modules.message as message
import logging

logger = logging.getLogger(__name__)

SLEEP_BETWEEN_ADDR = 10 #SECONDS
LIFETIME_OF_FORWARD_SET =  5 * 60 #SECONDS

def getRandomAddress():
    # SET RANDOM ADDRESS
    return random.randint(0x0011, 0x0FFF)

class Node:

    def __init__(self, handler, address = -1):
        self.handler = handler
        self.messageIdCount = 0x0000
        if address == -1:
            address = getRandomAddress()
            self.randomAddr = True
        else:
            self.randomAddr = False
        self.setAddress(address, True)
        self.forwardedMessages = set()
        self.forwardSetTime = time.time()

    def setAddress(self, address, parse=False):
        if parse:
            self.address = "%04X" % address
        else:
            self.address = address
        logger.info("Set address to {} (Temporary: {})".format(self.address, str(self.randomAddr)))
        self.handler.serial.write("AT+ADDR=" + self.address)

    def onMessage(self, msg):
        logger.debug("Incomming message: {}".format(msg.toString()))

        if time.time() - self.forwardSetTime >= LIFETIME_OF_FORWARD_SET:
            logger.info("Clearing set of forwarded messages")
            self.forwardedMessages.clear()

        if(msg.dest == self.address):
            self.onOwnMessage(msg)
        elif not self.randomAddr: # ONLY FORWARD MESSAGES IF FIXED ADDRESS IS GIVEN
            self.forwardMessage(msg)

    def forwardMessage(self, msg):
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
        if(msg.src=="0000" and msg.code==message.Code.ADDRESS):
            if self.randomAddr:
                logger.info("Got new address: {}".format(msg.payload))
                self.randomAddr = False
                self.setAddress(msg.payload)
                self.sendMessage(message.addressAcknowledge(self.address))
        else:
            logger.info("Got message from '{}': {}".format(msg.src, msg.payload))

    def sendMessage(self, msg):
        msg.id="%04x" % self.messageIdCount
        messageString = msg.toString()
        logger.debug("Sending message '{}'".format(messageString))
        self.handler.serial.write('AT+SEND=' + str(len(messageString)))
        self.handler.serial.write(messageString)
        self.messageIdCount += 1
        return msg.id

    def requestAddress(self):
        addr = threading.Thread(target=self._requestAddress)
        addr.setDaemon(True)
        addr.start()

    def _requestAddress(self):
        while self.randomAddr:
            logger.info("Requesting address")
            self.sendMessage(message.addressRequest(self.address))
            time.sleep(SLEEP_BETWEEN_ADDR)

