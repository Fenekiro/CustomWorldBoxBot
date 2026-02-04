import aiosqlite

from app.sql_api.sql.settings import connection
from app.sql_api.sql.core.exceptions.players import *
from app.sql_api.sql.core.games import GamesSQL

games_sql = GamesSQL()


class PlayersSQL:
    GET_PLAYERS_QUERY = "SELECT * FROM players WHERE game_id = ?"
    GET_PLAYER_QUERY = "SELECT * FROM players WHERE game_id = ? AND discord_id = ?"
    INSERT_PLAYER_QUERY = """
        INSERT INTO players (
            game_id,
            discord_id,
            registration_message_discord_id, 
            country_name,
            capital_name,
            race,
            culture_name,
            researches,
            wars,
            is_eliminated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    DELETE_PLAYER_QUERY = "DELETE FROM players WHERE game_id = ? AND discord_id = ?"

    @staticmethod
    def verify_that_player_is_not_eliminated(player_data: dict) -> None:
        if player_data["is_eliminated"]:
            raise PlayerIsEliminatedError

    async def get_players(self, game_id: int) -> list[dict]:
        db_response: aiosqlite.Cursor = await connection.execute(
            self.GET_PLAYERS_QUERY,
            (game_id,)
        )

        return [
            {
                "game_id": player[0],
                "discord_id": player[1],
                "registration_message_discord_id": player[2],
                "country_name": player[3],
                "capital_name": player[4],
                "race": player[5],
                "culture_name": player[6],
                "researches": player[7],
                "wars": player[8],
                "is_eliminated": player[9]
            } for player in await db_response.fetchall()
        ]

    async def get_player(self, game_id: int, player_discord_id: int) -> dict | None:
        db_response: aiosqlite.Cursor = await connection.execute(
            self.GET_PLAYER_QUERY,
            (game_id, player_discord_id,)
        )
        player_data = await db_response.fetchone()

        if not player_data:
            raise PlayerNotFoundError

        return {
            "game_id": player_data[0],
            "discord_id": player_data[1],
            "registration_message_discord_id": player_data[2],
            "country_name": player_data[3],
            "capital_name": player_data[4],
            "race": player_data[5],
            "culture_name": player_data[6],
            "researches": player_data[7],
            "wars": player_data[8],
            "is_eliminated": player_data[9]
        }

    async def insert_player(self, game_id: int, player_data: dict) -> None:
        game = await games_sql.get_game(game_id)

        if not game["is_open_for_registration"]:
            raise GameRegistrationIsClosedError

        try:
            await self.get_player(game_id, player_data["discord_id"])

            raise PlayerAlreadyRegisteredError

        except PlayerNotFoundError:
            await connection.execute(
                self.INSERT_PLAYER_QUERY,
                (
                    game_id,
                    player_data["discord_id"],
                    player_data["registration_message_discord_id"],
                    player_data["country_name"],
                    player_data["capital_name"],
                    player_data["race"],
                    player_data["culture_name"],
                    "[]",
                    '{"cant_declare_war_until_timestamp": null, "wars": []}',
                    0
                )
            )
            await connection.commit()

    async def delete_player(self, game_id: int, player_discord_id: int) -> None:
        await self.get_player(game_id, player_discord_id)

        game = await games_sql.get_game(game_id)

        if not game["is_open_for_registration"]:
            raise GameRegistrationIsClosedError

        await connection.execute(
            self.DELETE_PLAYER_QUERY,
            (game_id, player_discord_id,)
        )
        await connection.commit()
