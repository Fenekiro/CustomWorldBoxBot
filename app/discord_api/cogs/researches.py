import time

from discord import slash_command, ApplicationContext, Embed
from discord.ext.commands import Cog, Bot

from app.discord_api.embed_colors import EmbedColors
from app.sql_api.core.exceptions.games import GameSessionIsClosedError
from app.discord_api.other import games_core, researches_core
from app.sql_api.sql.core.exceptions.games import GameNotFoundError
from app.sql_api.sql.core.exceptions.players import PlayerIsEliminatedError, PlayerNotFoundError
from app.sql_api.sql.core.exceptions.researches import AlreadyResearchingError, MutuallyExclusiveResearchError, \
    AlreadyResearchedError, RequiredResearchesNotCompletedError, ResearchNotFoundError, ItemCountBelowZeroError, \
    ResearchNotFoundInPlayerDataError, ProducingTwoSameItemsAtTheSameTimeError, ProducingTooManyItemsError, \
    ResearchNotFinishedError, ItemsPerResearchLimitError
from app.utils.config import config_class
from app.discord_api.other import get_admin_mentions, technology_production_tasks


class Researches(Cog):
    @slash_command(
        name="researches_tree",
        description="Показать древо исследований текущей игры"
    )
    async def researches_tree(self, ctx: ApplicationContext) -> None:
        try:
            game = await games_core.get_current_game()

            await ctx.respond(game.researches_image_link)
        except GameNotFoundError:
            await ctx.respond("❌ | Действие невозможно, поскольку игра не была выбрана хостом", ephemeral=True)

    @slash_command(
        name="player_researches",
        description="Показать свои исследования или исследования другого игрока"
    )
    async def player_researches(self, ctx: ApplicationContext) -> None:
        player_researches = await researches_core.get_player_researches(ctx.user.id)
        finished_researches_list = [
            f"`{r.research.id}` `{r.research.name}` `{r.item_count}`"
            for r in player_researches
            if time.time() > r.researching_until_timestamp > 100_000
        ]
        finished_researches_list_str = "\n".join(finished_researches_list)

        ongoing_research = await researches_core.get_player_ongoing_research(ctx.user.id)

        if not ongoing_research:
            ongoing_research_str = ""
        else:
            if (diff := ongoing_research.researching_until_timestamp - time.time()) > 0:
                time_left_to_complete = time.strftime(
                    "%M:%S",
                    time.gmtime(diff)
                )
            else:
                time_left_to_complete = time.strftime(
                    "%M:%S",
                    time.gmtime(ongoing_research.researching_until_timestamp)
                )

            ongoing_research_str = f"`{ongoing_research.research.id}` `{ongoing_research.research.name}` `{time_left_to_complete}`"

        ongoing_item_productions = await researches_core.get_player_ongoing_research_item_productions(ctx.user.id)
        ongoing_item_productions_list = [
            f"`{item.research.id}` `{item.research.name}` `{time.strftime("%M:%S", time.gmtime(item.producing_item_until_timestamp - time.time() if time.time() < item.producing_item_until_timestamp else item.producing_item_until_timestamp))}`"
            for item in ongoing_item_productions
        ] if ongoing_item_productions else None
        ongoing_item_productions_str = "\n".join(ongoing_item_productions_list) if ongoing_item_productions_list else ""

        whole_text = f"""
            **Текущее исследование (ID | Название | Время до завершения)**
            {ongoing_research_str}
            **Текущие производства технологий (ID | Название | Время до завершения)**
            {ongoing_item_productions_str}
            **Завершённые исследования (ID | Название | Кол-во созданных технологий)**
            {finished_researches_list_str} 
        """

        notification_embed = Embed(color=EmbedColors.CHEESE, description=whole_text)
        notification_embed.set_author(
            name=f"[📖] Исследования игрока {ctx.user.display_name}",
            icon_url=ctx.user.avatar.url
        )
        notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

        await ctx.respond(embed=notification_embed, ephemeral=True)

    @slash_command(
        name="start_player_research",
        description="Начать исследование технологии"
    )
    async def start_player_research(self, ctx: ApplicationContext, research_id: int) -> None:
        try:
            await researches_core.start_player_research(ctx.user.id, research_id)

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)
            research = await researches_core.get_player_ongoing_research(ctx.user.id)

            notification_embed = Embed(
                color=EmbedColors.CHEESE,
                description=f"Игрок {ctx.user.mention} начал исследование технологии `{research.research.name}`"
            )
            notification_embed.set_author(name="[📖] Новое исследование", icon_url=ctx.user.avatar.url)
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await ctx.respond("📖 | Вы начали исследование.", ephemeral=True)
            await events_channel.send(embed=notification_embed)

        except GameSessionIsClosedError:
            await ctx.respond("❌ | Вы не можете совершать игровые действия вне игровой сессии.", ephemeral=True)
        except PlayerIsEliminatedError:
            await ctx.respond("❌ | Вы не можете начать исследование, поскольку вы выбыли из игры.", ephemeral=True)
        except PlayerNotFoundError:
            await ctx.respond("❌ | Вы не можете начать исследование, поскольку не участвуете в игре.", ephemeral=True)
        except AlreadyResearchingError:
            await ctx.respond("❌ | Данное исследование уже в процессе.", ephemeral=True)
        except ResearchNotFoundError:
            await ctx.respond("❌ | Данноого исследования нет в древе исследований текущей игры", ephemeral=True)
        except MutuallyExclusiveResearchError:
            await ctx.respond(
                "❌ | Вы не можете начать данное исследование, поскольку оно является взаимоисключающим с тем, которое вы уже провели.",
                ephemeral=True
            )
        except RequiredResearchesNotCompletedError:
            await ctx.respond(
                "❌ | Вы не можете начать данное исследование, поскольку не завершили предыдущие в древе исследований.",
                ephemeral=True
            )
        except AlreadyResearchedError:
            await ctx.respond("❌ | Вы уже завершили данное исследование.", ephemeral=True)

    @slash_command(
        name="cancel_player_ongoing_research",
        description="Отменить идущее исследование"
    )
    async def cancel_player_ongoing_research(self, ctx: ApplicationContext) -> None:
        try:
            ongoing_research = await researches_core.get_player_ongoing_research(ctx.user.id)

            if not ongoing_research:
                await ctx.respond("❌ | У вас нет текущих исследований.", ephemeral=True)

                return

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)

            notification_embed = Embed(
                color=EmbedColors.RED,
                description=f"Игрок {ctx.user.mention} отменил исследование технологии `{ongoing_research.research.name}`"
            )
            notification_embed.set_author(name="[📖] Отмена исследования", icon_url=ctx.user.avatar.url)
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await researches_core.cancel_player_ongoing_research(ctx.user.id)
            await ctx.respond("✅ | Вы отменили текущее исследование.", ephemeral=True)
            await events_channel.send(embed=notification_embed)
        except GameSessionIsClosedError:
            await ctx.respond("❌ | Вы не можете совершать игровые действия вне игровой сессии.", ephemeral=True)
        except PlayerIsEliminatedError:
            await ctx.respond("❌ | Вы не можете отменить исследование, поскольку вы выбыли из игры.", ephemeral=True)
        except PlayerNotFoundError:
            await ctx.respond("❌ | Вы не можете отменить исследование, поскольку не участвуете в игре.", ephemeral=True)

    @slash_command(
        name="start_technology_production"
    )
    async def start_producing_researched_item(self, ctx: ApplicationContext, technology_id: int) -> None:
        research_ = [r for r in await researches_core.get_game_researches() if r.id == technology_id]

        if not research_:
            await ctx.respond("❌ | Исследования не существует.", ephemeral=True)

            return
        else:
            research = research_[0]

        events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)

        notification_embed = Embed(
            color=EmbedColors.CHEESE,
            description=f"Игрок {ctx.user.mention} начал производство технологии `{research.name}`"
        )
        notification_embed.set_author(name="[💡] Производство технологии", icon_url=ctx.user.avatar.url)
        notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

        msg_1 = await (await ctx.respond("💡 | Вы начали производство технологии.", ephemeral=True)).original_response()
        msg_2 = ctx.bot.get_message((await events_channel.send(embed=notification_embed)).id)

        try:
            task = researches_core.start_player_producing_researched_item(ctx.user.id, technology_id)
            technology_production_tasks.append(task)

            await technology_production_tasks[-1]
        except ProducingTwoSameItemsAtTheSameTimeError:
            await ctx.respond(
                "❌ | Вы не можете производить несколько экземпляров одной технологии одновременно.",
                ephemeral=True
            )
            await msg_1.delete()
            await msg_2.delete()
        except ProducingTooManyItemsError:
            await ctx.respond(
                "❌ | Вы не можете производить больше 3 технологий одновременно.",
                ephemeral=True
            )
            await msg_1.delete()
            await msg_2.delete()
        except ResearchNotFoundInPlayerDataError:
            await ctx.respond(
                "❌ | Вы не можете производить данную технологию, поскольку вы её не исследовали.",
                ephemeral=True
            )
            await msg_1.delete()
            await msg_2.delete()
        except ResearchNotFinishedError:
            await ctx.respond(
                "❌ | Вы не можете производить данную технологию, поскольку ещё не закончили её исследовать.",
                ephemeral=True
            )
            await msg_1.delete()
            await msg_2.delete()
        except ItemsPerResearchLimitError:
            await ctx.respond(
                "❌ | Вы не можете производить более 3 экземпляров одной технологии.",
                ephemeral=True
            )
            await msg_1.delete()
            await msg_2.delete()
        except GameSessionIsClosedError:
            await ctx.respond("❌ | Вы не можете совершать игровые действия вне игровой сессии.", ephemeral=True)
            await msg_1.delete()
            await msg_2.delete()
        except PlayerIsEliminatedError:
            await ctx.respond("❌ | Вы не можете создавать технологию, поскольку уже выбыли из игры.", ephemeral=True)
            await msg_1.delete()
            await msg_2.delete()
        except PlayerNotFoundError:
            await ctx.respond("❌ | Вы не можете создавать технологию, поскольку не участвуете в игре.", ephemeral=True)
            await msg_1.delete()
            await msg_2.delete()

    @slash_command(
        name="use_technology",
        description="Использовать созданную технологию"
    )
    async def use_researched_item(self, ctx: ApplicationContext, technology_id: int, description: str) -> None:
        try:
            research_item_ = [r for r in await researches_core.get_game_researches() if r.id == technology_id]

            if not research_item_:
                await ctx.respond("❌ | Неизвестная технология.", ephemeral=True)

                return
            else:
                research_item = research_item_[0]

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)

            notification_embed = Embed(
                color=EmbedColors.CHEESE,
                description=f"Игрок {ctx.user.mention} использовал технологию `{research_item.name}`\n\n**Комментарий**\n" + description
            )
            notification_embed.set_author(name="[📖] Отмена исследования", icon_url=ctx.user.avatar.url)
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await researches_core.player_use_item(ctx.user.id, technology_id)
            await ctx.respond("✅ | Вы использовали технологию.", ephemeral=True)
            await events_channel.send(content=get_admin_mentions(), embed=notification_embed)

        except ItemCountBelowZeroError:
            await ctx.respond(
                "❌ | Вы не можете использовать данную технологию, поскольку у вас осталось 0 созданных технологий данного типа.",
                ephemeral=True
            )
        except ResearchNotFoundInPlayerDataError:
            await ctx.respond(
                "❌ | Вы не можете использовать данную технологию, поскольку вы её не исследовали.",
                ephemeral=True
            )
        except GameSessionIsClosedError:
            await ctx.respond("❌ | Вы не можете совершать игровые действия вне игровой сессии.", ephemeral=True)
        except PlayerIsEliminatedError:
            await ctx.respond("❌ | Вы не можете использовать технологию, поскольку уже выбыли из игры.", ephemeral=True)
        except PlayerNotFoundError:
            await ctx.respond("❌ | Вы не можете использовать технологию, поскольку не участвуете в игре.", ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(Researches(bot))
