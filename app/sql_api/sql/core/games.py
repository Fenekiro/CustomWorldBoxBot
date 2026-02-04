import aiosqlite
import time
import ujson

from app.sql_api.sql.settings import connection
from app.sql_api.sql.core.exceptions.games import *


class GamesSQL:
    GET_GAMES_QUERY = "SELECT * FROM games"
    GET_GAME_QUERY = "SELECT * FROM games WHERE id = ?"
    INSERT_NEW_GAME_QUERY = """
        INSERT INTO games(
            name,
            start_date_timestamp,
            end_date_timestamp,
            researches,
            researches_image_link,
            winners,
            image,
            is_open_for_registration,
            is_finished
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    TOGGLE_GAME_REGISTRATION_STATUS_QUERY = "UPDATE games SET is_open_for_registration = ? WHERE id = ?"
    FINISH_GAME_QUERY = "UPDATE games SET end_date_timestamp = ?, winners = ?, image = ?, is_finished = ? WHERE id = ?"
    DELETE_GAME_QUERY = "DELETE FROM games WHERE id = ?"
    REMOVE_ALL_GAME_PLAYERS = "DELETE FROM players WHERE game_id = ?"

    async def get_games(self) -> list[dict]:
        db_response: aiosqlite.Cursor = await connection.execute(self.GET_GAMES_QUERY)

        return [
            {
                "id": game[0],
                "name": game[1],
                "start_date_timestamp": game[2],
                "end_date_timestamp": game[3],
                "researches": game[4],
                "researches_image_link": game[5],
                "winners": game[6],
                "image": game[7],
                "is_open_for_registration": game[8],
                "is_finished": game[9],
            } for game in await db_response.fetchall()
        ]

    async def get_game(self, game_id: int) -> dict:
        db_response: aiosqlite.Cursor = await connection.execute(
            self.GET_GAME_QUERY,
            (game_id,)
        )
        game_data = await db_response.fetchone()

        if not game_data:
            raise GameNotFoundError

        return {
            "id": game_data[0],
            "name": game_data[1],
            "start_date_timestamp": game_data[2],
            "end_date_timestamp": game_data[3],
            "researches": game_data[4],
            "researches_image_link": game_data[5],
            "winners": game_data[6],
            "image": game_data[7],
            "is_open_for_registration": game_data[8],
            "is_finished": game_data[9],
        }

    async def insert_new_game(self, name: str, researches: list[dict], researches_image_link: str) -> None:
        await connection.execute(
            self.INSERT_NEW_GAME_QUERY,
            (name, time.time(), None, ujson.dumps(researches), researches_image_link, "[]", "", 1, 0,)
        )
        await connection.commit()

    async def toggle_players_registration_status(self, game_id: int, **kwargs) -> None:
        await self.get_game(game_id)

        if kwargs["task"] == "open":
            await connection.execute(
                self.TOGGLE_GAME_REGISTRATION_STATUS_QUERY,
                (1, game_id)
            )
        elif kwargs["task"] == "close":
            await connection.execute(
                self.TOGGLE_GAME_REGISTRATION_STATUS_QUERY,
                (0, game_id)
            )

        await connection.commit()

    async def finish_game(self, game_id: int, winners: list[int], image_link: str) -> None:
        await self.get_game(game_id)
        await connection.execute(
            self.FINISH_GAME_QUERY,
            (time.time(), ujson.dumps(winners), image_link, 1, game_id)
        )
        await connection.commit()

    async def delete_game(self, game_id: int) -> None:
        await self.get_game(game_id)
        await connection.execute(
            self.DELETE_GAME_QUERY,
            (game_id,)
        )
        await connection.execute(
            self.REMOVE_ALL_GAME_PLAYERS,
            (game_id,)
        )
        await connection.commit()
