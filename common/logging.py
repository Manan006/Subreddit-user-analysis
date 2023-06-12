class logger:
    def __init__(self, name: str = __name__):
        import os
        import logging
        import logging.handlers
        import queue
        import typing
        self.os = os
        self.logging = logging
        self.typing = typing
        self.queue = queue.Queue(-1)
        self.name = name
        self.queue_handler = self.logging.handlers.QueueHandler(self.queue)
        try:
            from .essential import essentials
        except ImportError:
            import sys
            sys.path.append("..")
            from common.essential import essentials
        self.essentials = essentials
        essentials()
        self.logging.basicConfig(level=self.logging.WARNING)
        try:
            logger = self.logging.getLogger(name)
            if self.os.getenv("LOG_LEVEL") == "2":
                level = self.logging.DEBUG
            elif self.os.getenv("LOG_LEVEL") == "1":
                level = self.logging.INFO
            else:
                level = self.logging.WARNING
            formatter = self.logging.Formatter(
                '%(asctime)s:%(name)s:%(levelname)s:%(message)s')
            handlers = []
            logger.setLevel(level)
            if None not in (self.os.getenv("LOG_FILE"), self.os.getenv("LOG_FLE_MAX_SIZE"), self.os.getenv("LOG_BACKUP_COUNT")):
                handler = self.logging.FileHandler(
                    self.os.getenv('LOG_FILE'), mode='w')
                handler.setFormatter(formatter)
                handler.setLevel(level)
                handlers.append(handler)
            if os.getenv("ENABLE_STREAM_HANDLER") == "1":
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
        self.listener.start()

    def __del__(self):
        try:
            self.listener.stop()
        except:
            pass

    def handle(self, level: str, *args):
        exec(f"self.logger.{level}(*args)")

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
