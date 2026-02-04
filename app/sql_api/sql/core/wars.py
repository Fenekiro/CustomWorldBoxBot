import ujson
import time

from app.sql_api.sql.settings import connection
from app.sql_api.sql.core.exceptions.wars import *
from app.sql_api.sql.core.players import PlayersSQL

players_sql = PlayersSQL()


class WarsSQL:
    UPDATE_WAR_STATUS_QUERY = "UPDATE players SET wars = ? WHERE game_id = ? AND discord_id = ?"
    ELIMINATE_PLAYER_QUERY = "UPDATE players SET is_eliminated = 1 WHERE game_id = ? AND discord_id = ?"
    REVIVE_PLAYER_QUERY = "UPDATE players SET is_eliminated = 0 WHERE game_id = ? AND discord_id = ?"

    async def declare_war(self, game_id: int, aggressor_discord_id: int, defender_discord_id: int) -> None:
        aggressor = await players_sql.get_player(game_id, aggressor_discord_id)
        defender = await players_sql.get_player(game_id, defender_discord_id)

        players_sql.verify_that_player_is_not_eliminated(aggressor)
        players_sql.verify_that_player_is_not_eliminated(defender)

        aggressor_wars: dict = ujson.loads(aggressor["wars"])
        defender_wars: dict = ujson.loads(defender["wars"])

        if len(aggressor_wars["wars"]) > 0:
            raise AlreadyInWarError

        if len(defender_wars["wars"]) == 2:
            raise PlayerWarLimitError

        if aggressor_wars["cant_declare_war_until_timestamp"]:
            if time.time() < aggressor_wars["cant_declare_war_until_timestamp"]:
                raise WarCooldownNotFinishedError

        new_war = {
            "aggressor": aggressor["discord_id"],
            "defender": defender["discord_id"]
        }

        aggressor_wars["wars"].append(new_war)
        defender_wars["wars"].append(new_war)

        await connection.execute(
            self.UPDATE_WAR_STATUS_QUERY,
            (ujson.dumps(aggressor_wars), game_id, aggressor_discord_id,)
        )
        await connection.execute(
            self.UPDATE_WAR_STATUS_QUERY,
            (ujson.dumps(defender_wars), game_id, defender_discord_id,)
        )
        await connection.commit()

    async def make_truce(self, game_id: int, player_1_discord_id: int, player_2_discord_id: int) -> None:
        player_1 = await players_sql.get_player(game_id, player_1_discord_id)
        player_2 = await players_sql.get_player(game_id, player_2_discord_id)

        player_1_wars: dict = ujson.loads(player_1["wars"])
        player_2_wars: dict = ujson.loads(player_2["wars"])

        passed_war = [
            war for war in player_1_wars["wars"]
            if len(set(war.values()) & {player_1_discord_id, player_2_discord_id}) == 2
        ]

        if not passed_war:
            raise InvalidWarError

        passed_war = passed_war[0]

        if passed_war["aggressor"] == player_1_discord_id:
            player_1_wars["cant_declare_war_until_timestamp"] = time.time() + 30 * 60
        else:
            player_2_wars["cant_declare_war_until_timestamp"] = time.time() + 30 * 60

        player_1_wars["wars"].remove(passed_war)
        player_2_wars["wars"].remove(passed_war)

        await connection.execute(
            self.UPDATE_WAR_STATUS_QUERY,
            (ujson.dumps(player_1_wars), game_id, player_1_discord_id,)
        )
        await connection.execute(
            self.UPDATE_WAR_STATUS_QUERY,
            (ujson.dumps(player_2_wars), game_id, player_2_discord_id,)
        )
        await connection.commit()

    async def eliminate_player(self, game_id: int, player_discord_id: int) -> None:
        player = await players_sql.get_player(game_id, player_discord_id)
        player_wars: dict = ujson.loads(player["wars"])

        for war in player_wars["wars"]:
            await self.make_truce(game_id, war["aggressor"], war["defender"])

        await connection.execute(
            self.ELIMINATE_PLAYER_QUERY,
            (game_id, player_discord_id)
        )
        await connection.commit()

    async def revive_player(self, game_id: int, player_discord_id: int) -> None:
        player = await players_sql.get_player(game_id, player_discord_id)

        if not player["is_eliminated"]:
            raise PlayerIsNotEliminatedError

        await connection.execute(
            self.REVIVE_PLAYER_QUERY,
            (game_id, player_discord_id)
        )
        await connection.commit()

    async def toggle_war_cooldown(self, game_id: int, player_discord_id: int) -> None:
        player = await players_sql.get_player(game_id, player_discord_id)
        player_wars: dict = ujson.loads(player["wars"])

        if player_wars["cant_declare_war_until_timestamp"]:
            if time.time() < player_wars["cant_declare_war_until_timestamp"]:
                player_wars["cant_declare_war_until_timestamp"] -= time.time()
            elif player_wars["cant_declare_war_until_timestamp"] < 100_000:
                player_wars["cant_declare_war_until_timestamp"] += time.time()

        await connection.execute(
            self.UPDATE_WAR_STATUS_QUERY,
            (ujson.dumps(player_wars), game_id, player_discord_id)
        )
        await connection.commit()
