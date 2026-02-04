from discord import ApplicationContext, Interaction

from app.sql_api.core.players import PlayersCore
from app.sql_api.core.games import GamesCore
from app.sql_api.core.wars import WarsCore
from app.sql_api.core.researches import ResearchesCore

from app.utils.config import config_class

players_core: PlayersCore = PlayersCore()
games_core: GamesCore = GamesCore()
wars_core: WarsCore = WarsCore()
researches_core: ResearchesCore = ResearchesCore()

technology_production_tasks = []


async def verify_admin(ctx: ApplicationContext | Interaction):
    if ctx.user.id not in config_class.data.admin_ids:
        await ctx.respond("❌ | У вас нет прав на данное действие.", ephemeral=True)

        return False

    return True


def get_admin_mentions() -> str:
    admin_mentions = [f"<@{admin_id}>" for admin_id in config_class.data.admin_ids]

    return "||" + " ".join(admin_mentions) + "||"


def get_game_role_mention() -> str:
    return f"||<@&{config_class.data.game_role_id}>||"


async def verify_commands_channel(ctx: ApplicationContext) -> bool:
    if ctx.channel.id != config_class.data.commands_chat_id:
        await ctx.respond("Не тот канал.", ephemeral=True)

        return False

    return True
