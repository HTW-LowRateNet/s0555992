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
    
    ser = serial.SerialInterface(port)

    logging.getLogger("modules.serial_interface").setLevel(logging.INFO)

    global handler
    handler = NodeHandler(ser)
    handler.start()

    while 1:
        input_val = input("")
        if input_val == 'exit':
            handler.shutdown()
            exit()
        elif (input_val.startswith("AT")):
            ser.write(input_val)
        else:
            parts = input_val.split(':')
            if len(parts) == 2:
                handler.sendMessage(parts[0], parts[1])

# MAIN METHOD HANDLING
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        try:
            serial.writeLock.release()
        except RuntimeError:
            pass
        try: 
            handler
        except NameError:
            pass
        else:
            handler.shutdown()