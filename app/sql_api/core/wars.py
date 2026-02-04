from app.sql_api.sql.core.wars import WarsSQL

from app.sql_api.core.games import GamesCore
from app.sql_api.core.players import PlayersCore

from app.utils.config import config_class

games_core = GamesCore()
players_core = PlayersCore()


class WarsCore:
    def __init__(self) -> None:
        self.sql_handler = WarsSQL()
        self.verify_current_game = games_core.verify_current_game

    async def declare_war(self, aggressor_discord_id: int, defender_discord_id: int) -> None:
        games_core.verify_game_session()

        await self.sql_handler.declare_war(config_class.data.current_game_id, aggressor_discord_id, defender_discord_id)

    async def make_truce(self, player_1_discord_id: int, player_2_discord_id: int) -> None:
        games_core.verify_game_session()

        await self.sql_handler.make_truce(config_class.data.current_game_id, player_1_discord_id, player_2_discord_id)

    async def eliminate_player(self, player_discord_id: int) -> None:
        games_core.verify_game_session()

        await self.sql_handler.eliminate_player(config_class.data.current_game_id, player_discord_id)

    async def revive_player(self, player_discord_id: int) -> None:
        games_core.verify_game_session()

        await self.sql_handler.revive_player(config_class.data.current_game_id, player_discord_id)

    async def toggle_war_cooldowns(self) -> None:
        for player in await players_core.get_players():
            await self.sql_handler.toggle_war_cooldown(config_class.data.current_game_id, player.discord_id)
