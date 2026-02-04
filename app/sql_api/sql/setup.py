import asyncio
from settings import connection


class Setup:
    SETUP_GAMES_TABLE_QUERY = """
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            start_date_timestamp REAL,
            end_date_timestamp REAL,
            researches TEXT,
            researches_image_link TEXT, 
            winners TEXT,
            image TEXT,
            is_open_for_registration SMALLINT,
            is_finished SMALLINT
        )
    """
    SETUP_PLAYERS_TABLE_QUERY = """
        CREATE TABLE IF NOT EXISTS players (
            game_id INTEGER,
            discord_id INTEGER,
            registration_message_discord_id TEXT, 
            country_name TEXT,
            capital_name TEXT,
            race TEXT,
            culture_name TEXT,
            researches TEXT,
            wars TEXT,
            is_eliminated SMALLINT
        ) 
    """

    async def setup(self) -> None:
        await asyncio.gather(
            self.__setup_games_table(),
            self.__setup_players_table()
        )

    async def __setup_games_table(self) -> None:
        await connection.execute(self.SETUP_GAMES_TABLE_QUERY)

    async def __setup_players_table(self) -> None:
        await connection.execute(self.SETUP_PLAYERS_TABLE_QUERY)


setup_sql = Setup()

asyncio.run(setup_sql.setup())
