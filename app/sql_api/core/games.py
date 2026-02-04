from app.sql_api.sql.core.exceptions.games import GameNotFoundError
from app.sql_api.sql.core.games import GamesSQL

from app.sql_api.core.types.games import *
from app.sql_api.core.types.researches import ResearchCore
from app.sql_api.core.exceptions.games import *

from app.utils.config import *


class GamesCore:
    def __init__(self) -> None:
        self.sql_handler = GamesSQL()

    async def select_game(self, game_id: int | None) -> None:
        if config_class.data.game_session_is_open:
            raise GameSessionIsNotClosedError

        if game_id is not None:
            await self.sql_handler.get_game(game_id)

        config_class.data.current_game_id = game_id
        config_class.update_json_file()

    async def get_games(self) -> list[GameCore]:
        return [self.__parse_game_from_dict(game_sql) for game_sql in await self.sql_handler.get_games()]

    async def get_current_game(self) -> GameCore:
        game_sql = await self.sql_handler.get_game(config_class.data.current_game_id)

        return self.__parse_game_from_dict(game_sql)

    @staticmethod
    def verify_current_game() -> None:
        if config_class.data.current_game_id is None:
            raise GameNotFoundError

    @staticmethod
    def verify_game_session() -> None:
        if not config_class.data.game_session_is_open:
            raise GameSessionIsClosedError

    async def add_new_game(self, name: str, researches: list[dict], researches_image_link: str) -> None:
        await self.sql_handler.insert_new_game(name, researches, researches_image_link)

    async def open_registration_for_current_game(self) -> None:
        await self.sql_handler.toggle_players_registration_status(config_class.data.current_game_id, task="open")

    async def close_registration_for_current_game(self) -> None:
        await self.sql_handler.toggle_players_registration_status(config_class.data.current_game_id, task="close")

    async def finish_current_game(self, winners: list[int], image_link: str) -> None:
        await self.sql_handler.finish_game(config_class.data.current_game_id, winners, image_link)

    async def delete_current_game(self) -> None:
        await self.sql_handler.delete_game(config_class.data.current_game_id)
        await self.select_game(None)

    async def start_game_session(self) -> None:
        self.verify_current_game()

        if config_class.data.game_session_is_open:
            raise GameSessionIsNotClosedError

        config_class.data.game_session_is_open = True
        config_class.update_json_file()

    async def close_game_session(self) -> None:
        self.verify_current_game()

        if not config_class.data.game_session_is_open:
            raise GameSessionIsClosedError

        config_class.data.game_session_is_open = False
        config_class.update_json_file()

    @staticmethod
    def __parse_game_from_dict(game_data: dict) -> GameCore:
        dict_researches: list[dict] = ujson.loads(game_data["researches"])

        researches = [
            ResearchCore(
                research["id"],
                research["name"],
                research["minutes_to_complete"],
                research["required_researches"],
                research["mutually_exclusive_researches"]
            ) for research in dict_researches
        ]

        game_core = GameCore(
            game_data["id"],
            game_data["name"],
            game_data["start_date_timestamp"],
            game_data["end_date_timestamp"],
            researches,
            game_data["researches_image_link"],
            ujson.loads(game_data["winners"]),
            game_data["image"],
            game_data["is_open_for_registration"] == 1,
            game_data["is_finished"] == 1
        )

        return game_core
