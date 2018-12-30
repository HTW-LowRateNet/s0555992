from enum import Enum
import logging


logger = logging.getLogger(__name__)

class Code(Enum):
    COORD_DISCOVERY = 'CDIS'
    COORD_ALIVE = 'ALIV'
    ADDRESS = 'ADDR'
    ADDRESS_ACK = 'AACK'
    NETWORK_RESET = 'NRST'
    MESSAGE = 'MSSG'    

def parseMessage(text):
    #LR,sender,lng,text(code, id, ttl, hops, srcAddr, destAddress, payload)
    logger.debug("Parsing message " + text)
    try:
        parts = text.split(',')
        code = Code(parts[3])
        id = parts[4]
        ttl = int(parts[5])
        hops = int(parts[6])
        src = parts[7]
        dest = parts[8]
        payload = parts[9]

        return Message(code, src, dest, payload, id, ttl, hops)
    except Exception as e:
        logger.warn("Failed to parse message " + e)
        raise ValueError("Invalid message format")

def discoverCoordinator(src):
    return Message(Code.COORD_DISCOVERY, src, "0000", "")

def coordinatorHeartbeat():
    return Message(Code.COORD_ALIVE, "0000", "FFFF", "")

def addressRequest(src):
    return Message(Code.ADDRESS, src, "0000", "")

def addressResponse(dest, addr):
    return Message(Code.ADDRESS, "0000", dest, addr)

def addressAcknowledge(addr):
    return Message(Code.ADDRESS_ACK, addr, "0000", "")

def networkReset(src):
    return Message(Code.NETWORK_RESET, src, "FFFF", "")

def message(src, dest, content):
    return Message(Code.MESSAGE, src, dest, content)

class Message:

    def __init__(self, code, src, dest, payload, id=0, ttl=5, hops=0):
        self.code = code
        self.id = id
        self.ttl = ttl
        self.hops = hops
        self.src = src
        self.dest = dest
        self.payload = payload

    def toString(self):
        return str(self.code.value + "," + str(self.id) + "," + str(self.ttl) + "," + str(self.hops) + "," + self.src + "," + self.dest + "," + self.payload)