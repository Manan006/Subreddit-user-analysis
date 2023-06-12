import aiomysql
from typing import Any, Callable, Union, List
import asyncio
from .logging import logger
from .essential import essentials
import functools
import aiofiles

class mariadb:
    def __init__(self, clean_tables: Union[None, List[str]] = []) -> None:
        self.loop = asyncio.get_event_loop()
        if type(clean_tables) is str:
            self.clean_tables = (clean_tables,)
        else:
            self.clean_tables = clean_tables

        self.essentials = essentials
        essentials(self.loop)
        self.functools = functools
        self.logger = logger("mariadb")
        self.aiomysql = aiomysql
        self.files = aiofiles
        self.loop.run_until_complete(self.__ainit__())

    async def __ainit__(self) -> None:
        self.pool = await self.generate_mariadb_pool()
        self.logger.debug("Generated mariadb pool")
        self.conn = await self.pool.acquire()
        self.logger.debug("Generated mariadb internal connection")
        self.cursor = await self.conn.cursor()
        self.logger.debug("Generated mariadb internal cursor")
        await self.init_mariadb()
        if self.clean_tables is not None:
            await self.table_clean()
        await self.conn.commit()

    def pool_to_cursor(self, func: Callable[..., Any]):
        @self.functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            conn = None
            self.logger.debug(
                "Acquiring connection from pool and cursor from connection")
            try:
                conn = await self.pool.acquire()
            except Exception as e:
                self.logger.critical(
                    "Failed to acquire connection from pool. Waiting for 5*6 seconds (5 seconds * 6 tries)")
                self.logger.exception(e)
                for i in range(6):
                    try:
                        conn = await self.pool.acquire()
                    except aiomysql.err.OperationalError as e:
                        self.logger.critical(
                            f"Failed to acquire connection from pool. Waiting for {5*(6-i)} seconds")
                        await asyncio.sleep(5)
                    else:
                        break
                if conn is None:
                    self.logger.critical(
                        "Failed to acquire connection from pool. Exiting")
            cursor = await conn.cursor()
            self.logger.debug("Running target")
            try:
                result = await func(cursor, *args, *kwargs)
            except Exception as e:
                self.logger.critical("Failed to run target")
                self.logger.exception(e)
                await cursor.close()
                conn.close()
                await self.pool.release(conn)
                return
            await conn.commit()
            await cursor.close()
            conn.close()
            await self.pool.release(conn)
            return result
        return wrapper

    async def generate_mariadb_pool(self) -> aiomysql.pool.Pool:
        self.logger.info("Initializing mariadb")
        pool = await self.aiomysql.create_pool(host='localhost',
                                               port=3306,
                                               user='root',
                                               password='',
                                               db='AtheismIndia_Stats',
                                               autocommit=False,
                                               minsize=1,
                                               maxsize=450)
        return pool

    async def end(self) -> None:
        self.logger.info("Closing mariadb connection")
        await self.cursor.close()
        self.logger.debug("Closed mariadb internal cursor")
        self.conn.close()
        self.logger.debug("Closed mariadb internal connection")
        self.pool.close()
        self.logger.debug("Closed mariadb pool")
        self.logger.info("MariaDB module closed")

    async def init_mariadb(self) -> None:
        self.logger.info(("Initializing mariadb"))
        try:
            for query in await self.get_sql("init"):
                await self.cursor.execute(query)
        except Exception as e:
            self.logger.critical("Failed to create tables in mariadb")
            self.logger.exception(e)
            return
        self.logger.info("Initialized mariadb tables")

    async def table_clean(self) -> None:
        self.logger.info("Cleaning tables")
        try:
            for table in self.clean_tables:
                await self.cursor.execute(f"DELETE FROM {table}")
        except Exception as e:
            self.logger.critical("Failed to clean tables")
            self.logger.exception(e)

    async def get_sql(self, name: str):
        self.logger.info(f"Getting sql query: {name}.sql")
        try:
            async with self.files.open(f"sql/{name}.sql", mode="r") as f:
                query: str = await f.read()
        except Exception as e:
            self.logger.critical(f"Failed to get sql query: {name}.sql")
            self.logger.exception(e)
            return tuple()
        self.logger.info(f"Got sql query: {name}.sql")
        return tuple(filter(lambda x: x != "", query.strip().split(";")))
