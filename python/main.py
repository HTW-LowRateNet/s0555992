import modules.serial_interface as serial
from modules.node_handler import NodeHandler
import sys
import logging
import logging.config
import yaml

logger = logging.getLogger(__name__)

def setup_logging():
    with open('logging.yaml', 'rt') as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

def main():
    setup_logging()
    port = sys.argv[1]
    
    logger.info("Opening serial port {}".format(port))
    serial.initIOWrapper(sys.argv[1])

    global handler
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
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        handler.stop()