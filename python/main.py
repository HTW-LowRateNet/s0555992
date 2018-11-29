import modules.serial_interface as serial
from modules.node_handler import NodeHandler
import sys


def main():
    port = sys.argv[1]
    print("Opening serial port {}".format(port))
    serial.initIOWrapper(sys.argv[1])

    handler = NodeHandler()
    handler.start()

    while 1:
        input_val = input("")
        if input_val == 'exit':
            handler.stop()
            exit()
        else:
            serial.write(input_val + '\r\n')

# MAIN METHOD HANDLING
if __name__ == "__main__":
    main()