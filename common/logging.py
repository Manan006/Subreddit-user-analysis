from config import *
import os
import logging
import logging.handlers
import queue
import typing
try:
    from .essential import essentials
except ImportError:
    import sys
    sys.path.append("..")
    from common.essential import essentials

class logger: # Class which handles the logging
    def __init__(self, name: str = __name__):
        self.os = os
        self.logging = logging
        self.typing = typing
        self.queue = queue.Queue(-1) # The logger runs in a seperate thread to not block the asyncio loop
        self.name = name
        self.queue_handler = self.logging.handlers.QueueHandler(self.queue)
        self.essentials = essentials
        essentials()
        self.logging.basicConfig(level=self.logging.WARNING)
        try:
            logger = self.logging.getLogger(name)
            if str(LOG_LEVEL) == "2":
                level = self.logging.DEBUG
            elif str(LOG_LEVEL) == "1":
                level = self.logging.INFO
            else:
                level = self.logging.WARNING
            formatter = self.logging.Formatter(
                '%(asctime)s:%(name)s:%(levelname)s:%(message)s')
            handlers = []
            logger.setLevel(level)
            handler = self.logging.FileHandler(
                LOG_FILE, mode='w')
            handler.setFormatter(formatter)
            handler.setLevel(level)
            handlers.append(handler)
            if ENABLE_STREAM_HANDLER == "1": # Enable stream handler (Prints to console)
                logger.propagate = True
            else:
                logger.propagate = False
            logger.addHandler(self.queue_handler)
            print(handlers)
            self.listener = logging.handlers.QueueListener(
                self.queue, *handlers, respect_handler_level=True
            )
        except Exception as e:
            self.logging.critical(f"Failed to initialize logger for {name}")
            self.logging.exception(e)
            self.os.sys.exit(1)
        self.logger = logger
        self.listener.start() # Start the listener

    def __del__(self): # Stop the listener when the object is deleted
        try:
            self.listener.stop()
        except:
            pass

    def handle(self, level: str, *args): # Handles the methods called
        exec(f"self.logger.{level}(*args)")

###
### The following methods are just wrappers for the handle method
###

    def debug(self, *args):
        self.handle("debug", *args)

    def info(self, *args):
        self.handle("info", *args)

    def warning(self, *args):
        self.handle("warning", *args)

    def error(self, *args):
        self.handle("error", *args)

    def critical(self, *args):
        self.handle("critical", *args)

    def exception(self, *args):
        self.handle("exception", *args)
