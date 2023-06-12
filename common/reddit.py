import asyncpraw
import asyncio
from .essential import essentials
from .logging import logger
import os

class reddit(asyncpraw.Reddit):
    def __init__(self) -> None:
        self.essentials = essentials
        self.loop = asyncio.get_event_loop()
        essentials(self.loop)
        self.loop.run_until_complete(self.__ainit__())

    async def __ainit__(self) -> None:
        self.logger = logger("reddit")
        self.os = os
        self.asyncpraw = asyncpraw
        self.logger.info("Initializing reddit")
        try:
            self.asyncpraw.Reddit.__init__(self,
                                           client_id=self.os.getenv(
                                               "CLIENT_ID"),
                                           client_secret=self.os.getenv(
                                               "CLIENT_SECRET"),
                                           password=self.os.getenv(
                                               "PASSWORD"),
                                           user_agent=self.os.getenv(
                                               "USER_AGENT"),
                                           username=self.os.getenv(
                                               "USERNAME"),
                                           )
        except Exception as e:
            self.logger.critical("Failed to initialize reddit")
            self.logger.exception(e)
            self.logger.critical("Exiting")
            self.essentials.sys.exit(1)
        self.logger.info("Reddit initialized")

    async def end(self) -> None:
        self.logger.info("Closing reddit connection")
        await self.close()
        await self._core._requestor._http.close()
