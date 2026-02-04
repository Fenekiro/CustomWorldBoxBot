import ujson
import time

from app.sql_api.sql.core.players import PlayersSQL
from app.sql_api.sql.settings import connection
from app.sql_api.sql.core.exceptions.researches import *
from app.sql_api.sql.core.games import GamesSQL

players_sql = PlayersSQL()
games_sql = GamesSQL()


class ResearchesSQL:
    UPDATE_PLAYER_RESEARCHES_QUERY = "UPDATE players SET researches = ? WHERE game_id = ? AND discord_id = ?"

    async def get_player_ongoing_research(
        self, game_id: int, player_discord_id: int
    ) -> dict | None:
        player_researches = await self.__get_player_researches(game_id, player_discord_id)
        player_ongoing_researches = [
            research for research in player_researches if time.time() < research["researching_until_timestamp"]
        ]

        if not player_ongoing_researches:
            return

        return player_ongoing_researches[0]

    async def get_player_ongoing_research_item_productions(
        self, game_id: int, player_discord_id: int
    ) -> list[dict] | None:
        player_researches = await self.__get_player_researches(game_id, player_discord_id)

        player_ongoing_research_items_producing = [
            research for research in player_researches
            if research["producing_item_until_timestamp"] and time.time() < research["producing_item_until_timestamp"]
        ]

        if not player_ongoing_research_items_producing:
            return

        return player_ongoing_research_items_producing

    async def insert_player_research(self, game_id: int, player_discord_id: int, research_id: int) -> None:
        ongoing_research = await self.get_player_ongoing_research(game_id, player_discord_id)
        player = await players_sql.get_player(game_id, player_discord_id)

        players_sql.verify_that_player_is_not_eliminated(player)

        if ongoing_research:
            raise AlreadyResearchingError

        research_ = [res for res in await self.__get_game_researches(game_id) if res["id"] == research_id]

        if not research_:
            raise ResearchNotFoundError
        else:
            research = research_[0]

        player_researches = await self.__get_player_researches(game_id, player_discord_id)

        for player_research in player_researches:
            if research["id"] in player_research["research"]["mutually_exclusive_researches"]:
                raise MutuallyExclusiveResearchError

            if research["id"] == player_research["research"]["id"]:
                raise AlreadyResearchedError

        new_player_research = {
            "research": research,
            "item_count": 0,
            "researching_until_timestamp": time.time() + research["minutes_to_complete"] * 60,
            "producing_item_until_timestamp": None
        }
        required_researches_ids = new_player_research["research"]["required_researches"]
        player_researches_ids = [player_research["research"]["id"] for player_research in player_researches]

        if required_researches_ids and len(set(required_researches_ids) & set(player_researches_ids)) == 0:
            raise RequiredResearchesNotCompletedError

        player_researches.append(new_player_research)

        await self.__update_player_researches(game_id, player_discord_id, player_researches)

    async def remove_player_ongoing_research(self, game_id: int, player_discord_id: int) -> None:
        ongoing_research = await self.get_player_ongoing_research(game_id, player_discord_id)
        player_researches = await self.__get_player_researches(game_id, player_discord_id)
        player = await players_sql.get_player(game_id, player_discord_id)

        players_sql.verify_that_player_is_not_eliminated(player)

        player_researches.remove(ongoing_research)

        await self.__update_player_researches(game_id, player_discord_id, player_researches)

    async def insert_player_producing_researched_item(
        self, game_id: int, player_discord_id: int, research_id: int
    ) -> None:
        player_researches = await self.__get_player_researches(game_id, player_discord_id)
        player = await players_sql.get_player(game_id, player_discord_id)

        players_sql.verify_that_player_is_not_eliminated(player)

        needed_research_index = 0
        producing_items_count = 0

        for i in range(len(player_researches)):
            if player_researches[i]["research"]["id"] == research_id:
                needed_research_index = i

                if player_researches[i]["producing_item_until_timestamp"]:
                    if time.time() < player_researches[i]["producing_item_until_timestamp"]:
                        raise ProducingTwoSameItemsAtTheSameTimeError

            if player_researches[i]["producing_item_until_timestamp"]:
                if time.time() < player_researches[i]["producing_item_until_timestamp"]:
                    producing_items_count += 1

        if producing_items_count > 3:
            raise ProducingTooManyItemsError

        if not needed_research_index + 1:
            raise ResearchNotFoundInPlayerDataError

        needed_research = player_researches[needed_research_index]

        if needed_research["item_count"] == 3:
            raise ItemsPerResearchLimitError

        if time.time() < needed_research["researching_until_timestamp"]:
            raise ResearchNotFinishedError

        needed_research["producing_item_until_timestamp"] = time.time() + needed_research["research"]["minutes_to_complete"] * 60

        await self.__update_player_researches(game_id, player_discord_id, player_researches)

    async def update_player_researched_item_count(
        self, game_id: int, player_discord_id: int, research_id: int, **kwargs
    ) -> None:
        player_researches = await self.__get_player_researches(game_id, player_discord_id)
        player = await players_sql.get_player(game_id, player_discord_id)

        players_sql.verify_that_player_is_not_eliminated(player)

        needed_research_index = 0

        for i in range(len(player_researches)):
            if player_researches[i]["research"]["id"] == research_id:
                needed_research_index = i

                break

        if not needed_research_index + 1:
            raise ResearchNotFoundInPlayerDataError

        needed_research = player_researches[needed_research_index]

        if kwargs["task"] == "increase":
            needed_research["item_count"] += 1
        elif kwargs["task"] == "decrease":
            if needed_research["item_count"] == 0:
                raise ItemCountBelowZeroError

            needed_research["item_count"] -= 1

        await self.__update_player_researches(game_id, player_discord_id, player_researches)

    async def delay_player_current_research(self, game_id: int, player_discord_id: int) -> None:
        player_researches = await self.__get_player_researches(game_id, player_discord_id)

        for player_research in player_researches:
            if time.time() < player_research["researching_until_timestamp"]:
                player_research["researching_until_timestamp"] -= time.time()
                break

        await self.__update_player_researches(game_id, player_discord_id, player_researches)

    async def delay_player_item_production(self, game_id: int, player_discord_id: int) -> None:
        player_researches = await self.__get_player_researches(game_id, player_discord_id)

        for player_research in player_researches:
            if player_research["producing_item_until_timestamp"] and time.time() < player_research["producing_item_until_timestamp"]:
                player_research["producing_item_until_timestamp"] -= time.time()
                break

        await self.__update_player_researches(game_id, player_discord_id, player_researches)

    async def update_player_research_end_timestamp(
        self, game_id: int, player_discord_id: int, research_id: int, new_timestamp: float
    ) -> None:
        player_researches = await self.__get_player_researches(game_id, player_discord_id)

        for player_research in player_researches:
            if player_research["research"]["id"] == research_id:
                player_research["researching_until_timestamp"] = new_timestamp

                await self.__update_player_researches(game_id, player_discord_id, player_researches)

                return

    async def update_player_item_production_end_timestamp(
        self, game_id: int, player_discord_id: int, research_id: int, new_timestamp: float
    ) -> None:
        player_researches = await self.__get_player_researches(game_id, player_discord_id)

        for player_research in player_researches:
            if player_research["research"]["id"] == research_id:
                player_research["producing_item_until_timestamp"] = new_timestamp

                await self.__update_player_researches(game_id, player_discord_id, player_researches)

                return

    @staticmethod
    async def __get_game_researches(game_id: int) -> list[dict]:
        game = await games_sql.get_game(game_id)

        return ujson.loads(game["researches"])

    @staticmethod
    async def __get_player_researches(game_id: int, player_discord_id: int) -> list[dict]:
        player = await players_sql.get_player(game_id, player_discord_id)

        return ujson.loads(player["researches"])

    async def __update_player_researches(
        self, game_id: int, player_discord_id: int, player_researches: list[dict]
    ) -> None:
        await connection.execute(
            self.UPDATE_PLAYER_RESEARCHES_QUERY,
            (ujson.dumps(player_researches), game_id, player_discord_id,)
        )
        await connection.commit()
