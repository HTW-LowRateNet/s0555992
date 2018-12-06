import modules.serial_interface as serial
import threading
import time
import random

def getRandomAddress():
    # SET RANDOM ADDRESS
    address = "%04x" % random.randint(0x0001, 0x000F)
    return address

class Node:

    def __init__(self, address = getRandomAddress()):
        self.setAddress(address)

    def setAddress(self, address):
        self.address = address
        serial.write("AT+ADDR=" + address)

    def onMessage(self, message):
        print("Got message from '{}': {}".format(message.src, message.payload))

    def sendMessage(self, message):
        messageString = message.toString()
        print("Sending message '{}'".format(messageString))
        # TODO CHECK DESTINATION IN ROUTING TABLE
        #serial.write('AT+DEST=' + message.dest)
        serial.write('AT+SEND=' + str(len(messageString)))
        serial.write(messageString)
