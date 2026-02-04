import asyncio
import aiosqlite


class SqlSettings:
    def __init__(self) -> None:
        self.connection: None | aiosqlite.Connection = None
        self.db_path = __file__.replace("settings.py", "database.db")

        asyncio.run(self.__spawn_connection())

    async def __spawn_connection(self) -> None:
        self.connection = await aiosqlite.connect(self.db_path)


connection = SqlSettings().connection
