import modules.serial_interface as serial
import threading
import time
import random
import modules.message as message
import logging

logger = logging.getLogger(__name__)

def getRandomAddress():
    # SET RANDOM ADDRESS
    return random.randint(0x0001, 0x000F)

class Node:

    def __init__(self, address = getRandomAddress()):
        self.messageIdCount = 0x0000
        self.setAddress(address)
        self.forwardedMessages = set()

    def setAddress(self, address):
        self.address =  "%04x" % address
        serial.write("AT+ADDR=" + self.address)

    def onMessage(self, msg):
        logger.info("Got message from '{}': {}".format(msg.src, msg.payload))

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
                    set.add(msgId)
            else:
                logger.debug("Already forwarded message")

    def onOwnMessage(self, msg):
        if(msg.src=="0000" and msg.code==message.Code.ADDRESS):
            self.setAddress(msg.payload)
            self.sendMessage(message.addressAcknowledge(self.address))

    def sendMessage(self, msg):
        msg.id="%04x" % self.messageIdCount
        messageString = msg.toString()
        logger.debug("Sending message '{}'".format(messageString))
        serial.write('AT+SEND=' + str(len(messageString)))
        serial.write(messageString)
        self.messageIdCount += 1

    def requestAddress(self):
        self.sendMessage(message.addressRequest(self.address))