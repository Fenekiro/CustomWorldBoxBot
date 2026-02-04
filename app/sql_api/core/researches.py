import asyncio
import time

from app.sql_api.sql.core.researches import ResearchesSQL

from app.sql_api.core.players import PlayersCore
from app.sql_api.core.types.researches import *
from app.sql_api.core.games import GamesCore

from app.utils.config import config_class

players_core = PlayersCore()
games_core = GamesCore()


class ResearchesCore:
    def __init__(self) -> None:
        self.sql_handler = ResearchesSQL()

    @staticmethod
    async def get_game_researches() -> list[ResearchCore]:
        game = await games_core.get_current_game()

        return game.researches

    @staticmethod
    async def get_player_researches(player_discord_id: int) -> list[PlayerResearchCore]:
        player = await players_core.get_player(player_discord_id)

        return player.researches

    async def get_player_ongoing_research(self, player_discord_id: int) -> PlayerResearchCore | None:
        ongoing_research = [
            player_research for player_research
            in await self.get_player_researches(player_discord_id)
            if
            time.time() < player_research.researching_until_timestamp or player_research.researching_until_timestamp < 100_000
        ]

        if not ongoing_research:
            return

        return ongoing_research[0]

    async def get_player_ongoing_research_item_productions(
        self,
        player_discord_id: int
    ) -> list[PlayerResearchCore] | None:
        ongoing_item_productions = [
            player_research for player_research
            in await self.get_player_researches(player_discord_id)
            if player_research.producing_item_until_timestamp
            and (time.time() < player_research.producing_item_until_timestamp or player_research.producing_item_until_timestamp < 100_000)
        ]

        if not ongoing_item_productions:
            return

        return ongoing_item_productions

    async def start_player_research(self, player_discord_id: int, research_id: int) -> None:
        games_core.verify_game_session()

        await self.sql_handler.insert_player_research(
            config_class.data.current_game_id,
            player_discord_id,
            research_id
        )

    async def cancel_player_ongoing_research(self, player_discord_id: int) -> None:
        games_core.verify_game_session()

        await self.sql_handler.remove_player_ongoing_research(config_class.data.current_game_id, player_discord_id)

    async def start_player_producing_researched_item(
        self, player_discord_id: int, research_id: int, delayed: bool = False
    ) -> None:
        games_core.verify_game_session()

        if not delayed:
            await self.sql_handler.insert_player_producing_researched_item(
                config_class.data.current_game_id,
                player_discord_id,
                research_id
            )

        ongoing_player_item_production = [
            item for item in await self.get_player_ongoing_research_item_productions(player_discord_id)
            if item.research.id == research_id
        ][0]

        while time.time() < ongoing_player_item_production.producing_item_until_timestamp:
            await asyncio.sleep(0.5)

        await self.player_finish_item_production(player_discord_id, research_id)

    async def player_finish_item_production(self, player_discord_id: int, research_id: int) -> None:
        games_core.verify_game_session()

        await self.sql_handler.update_player_researched_item_count(
            config_class.data.current_game_id,
            player_discord_id,
            research_id,
            task="increase"
        )

    async def player_use_item(self, player_discord_id: int, research_id: int) -> None:
        games_core.verify_game_session()

        await self.sql_handler.update_player_researched_item_count(
            config_class.data.current_game_id,
            player_discord_id,
            research_id,
            task="decrease"
        )

    async def delay_players_current_researches(self) -> None:
        for player in await players_core.get_players():
            await self.sql_handler.delay_player_current_research(config_class.data.current_game_id, player.discord_id)

    async def delay_players_current_item_productions(self) -> None:
        for player in await players_core.get_players():
            await self.sql_handler.delay_player_item_production(config_class.data.current_game_id, player.discord_id)

    async def continue_delayed_players_researches(self) -> None:
        for player in await players_core.get_players():
            for player_research in player.researches:
                if player_research.researching_until_timestamp < 100_000:
                    await self.sql_handler.update_player_research_end_timestamp(
                        config_class.data.current_game_id,
                        player.discord_id,
                        player_research.research.id,
                        time.time() + player_research.researching_until_timestamp
                    )

    async def continue_delayed_players_item_productions(self) -> None:
        tasks = []

        for player in await players_core.get_players():
            for player_research in player.researches:
                if player_research.producing_item_until_timestamp and player_research.producing_item_until_timestamp < 100_000:
                    await self.sql_handler.update_player_item_production_end_timestamp(
                        config_class.data.current_game_id,
                        player.discord_id,
                        player_research.research.id,
                        time.time() + player_research.producing_item_until_timestamp
                    )

                    tasks.append(
                        self.start_player_producing_researched_item(
                            player.discord_id,
                            player_research.research.id,
                            delayed=True
                        )
                    )

                    break

        await asyncio.gather(*tasks)
