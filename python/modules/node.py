import modules.serial_interface as serial

class Node:

    def __init__(self, address):
        self.setAddress(address)

    def setAddress(self, address):
        self.address = address
        serial.write("AT+ADDR=" + address)

    def onMessage(self, sender, message):
        print("Got message from '{}': {}".format(sender, message))

    def sendMessage(self, receiver, message):
        print("Sending message '{}' to '{}'".format(message, receiver))
        serial.write('AT+DEST=' + receiver)
        serial.write('AT+SEND=' + str(len(message)))
        serial.write(message)