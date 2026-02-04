import ujson

from app.sql_api.sql.core.players import PlayersSQL

from app.sql_api.core.types.players import PlayerCore, PlayerRegisterData
from app.sql_api.core.types.wars import *
from app.sql_api.core.types.researches import *

from app.utils.config import config_class


class PlayersCore:
    def __init__(self) -> None:
        self.sql_handler = PlayersSQL()

    async def get_players(self) -> list[PlayerCore]:
        players_sql = await self.sql_handler.get_players(config_class.data.current_game_id)

        return [self.__parse_player_from_dict(player_sql) for player_sql in players_sql]

    async def get_player(self, player_discord_id: int) -> PlayerCore:
        player_sql = await self.sql_handler.get_player(config_class.data.current_game_id, player_discord_id)

        return self.__parse_player_from_dict(player_sql)

    async def register_player(self, player_data: PlayerRegisterData) -> None:
        await self.sql_handler.insert_player(
            config_class.data.current_game_id,
            {
                "discord_id": player_data.discord_id,
                "country_name": player_data.country_name,
                "registration_message_discord_id": player_data.registration_message_discord_id,
                "capital_name": player_data.capital_name,
                "race": player_data.race,
                "culture_name": player_data.culture_name
            }
        )

    async def delete_player(self, player_discord_id: int) -> None:
        await self.sql_handler.delete_player(config_class.data.current_game_id, player_discord_id)

    @staticmethod
    def __parse_player_from_dict(player_data: dict) -> PlayerCore:
        player_wars_dict = ujson.loads(player_data["wars"])
        player_researches_dict = ujson.loads(player_data["researches"])

        player_wars = PlayerWarsCore(player_wars_dict["cant_declare_war_until_timestamp"], [])
        player_researches: list[PlayerResearchCore] = []

        for war_dict in player_wars_dict["wars"]:
            player_wars.wars.append(WarCore(war_dict["aggressor"], war_dict["defender"]))

        for player_research_dict in player_researches_dict:
            research = ResearchCore(
                player_research_dict["research"]["id"],
                player_research_dict["research"]["name"],
                player_research_dict["research"]["minutes_to_complete"],
                player_research_dict["research"]["required_researches"],
                player_research_dict["research"]["mutually_exclusive_researches"]
            )
            player_research = PlayerResearchCore(
                research,
                player_research_dict["item_count"],
                player_research_dict["researching_until_timestamp"],
                player_research_dict["producing_item_until_timestamp"]
            )

            player_researches.append(player_research)

        return PlayerCore(
            player_data["game_id"],
            player_data["discord_id"],
            player_data["registration_message_discord_id"],
            player_data["country_name"],
            player_data["capital_name"],
            player_data["race"],
            player_data["culture_name"],
            player_researches,
            player_wars,
            player_data["is_eliminated"] == 1
        )
