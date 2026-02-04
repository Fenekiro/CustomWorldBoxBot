from datetime import datetime
import ujson

from discord import ApplicationContext
from discord.ext.commands import Cog, Bot, slash_command
from discord.ext.pages import Page, Paginator
from discord import Embed, Option, Member

from app.discord_api.embed_colors import EmbedColors
from app.discord_api.other import games_core, verify_commands_channel, verify_admin, get_game_role_mention

from app.sql_api.sql.core.exceptions.games import GameNotFoundError
from app.sql_api.core.exceptions.games import GameSessionIsNotClosedError

from app.utils.config import config_class

from app.discord_api.views.games import GameSessionView, GameDeleteView


class Games(Cog):
    @slash_command(
        name="games_list",
        description="Показать все игры"
    )
    async def games_list(self, ctx: ApplicationContext) -> None:
        games = await games_core.get_games()
        pages = []

        if not await verify_commands_channel(ctx):
            return

        for game in games:
            start_date = datetime.fromtimestamp(game.start_date_timestamp).strftime("%d.%m.%Y %H:%M")
            end_date = datetime.fromtimestamp(game.end_date_timestamp).strftime("%d.%m.%Y %H:%M") if game.end_date_timestamp else "❔"
            winners = "\n".join([f"<@{winner}>" for winner in game.winners]) if game.winners else "❔"
            image = game.image if game.image else ""
            is_opened_for_registration = "✅" if game.is_open_for_registration else "❌"
            is_finished = "✅" if game.is_finished else "❌"

            game_embed = Embed(title=f'Игра "{game.name}"', color=EmbedColors.CHEESE)
            game_embed.add_field(name="ID", value=str(game.id))
            game_embed.add_field(name="Начало игры", value=start_date)
            game_embed.add_field(name="Конец игры", value=end_date)
            game_embed.add_field(name="Победители", value=winners)
            game_embed.set_image(url=image)
            game_embed.add_field(name="Открыта для регистрации", value=is_opened_for_registration)
            game_embed.add_field(name="Завершена", value=is_finished)

            researches_image_embed = Embed(
                title="Исследования",
                image=game.researches_image_link,
                color=EmbedColors.CHEESE
            )

            pages.append(Page(embeds=[game_embed, researches_image_embed]))

        paginator = Paginator(pages=pages)

        await paginator.respond(ctx.interaction)

    @slash_command(
        name="start_new_game",
        description="Начать новую игру"
    )
    async def start_new_game(
        self,
        ctx: ApplicationContext,
        name: str,
        researches_image_link: str
    ) -> None:
        try:
            if not await verify_admin(ctx):
                return

            with open(r"C:\Users\Saphy\PycharmProjects\WorldboxBot\app\researches.json", "r", encoding="utf-8") as file:
                researches = ujson.loads(file.read())

            await games_core.add_new_game(name, researches, researches_image_link)
            await ctx.respond(
                f"✅ | Новая игра под названием {name} была создана и добавлена в базу данных.",
                ephemeral=True
            )

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)

            notification_embed = Embed(
                title="[🔧] Техническое уведомление",
                color=EmbedColors.GREEN,
                description=f"Новая игра под под названием **{name}** была создана и внесена в базу данных",
            )

            await events_channel.send(embed=notification_embed)

        except Exception as e:
            print(e)

            await ctx.respond("❌ | Неверный JSON формат.", ephemeral=True)

    @slash_command(
        name="open_game_registration",
        description="Открыть регистрацию на текущую игру для новых игроков"
    )
    async def open_game_registration(self, ctx: ApplicationContext) -> None:
        try:
            if not await verify_admin(ctx):
                return

            await games_core.open_registration_for_current_game()
            await ctx.respond("✅ | Регистрация на игру открыта.", ephemeral=True)

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)
            notification_embed = Embed(
                title="[🔧] Техническое уведомление",
                color=EmbedColors.GREEN,
                description=f"Была открыта регистрация на текущую игру"
            )
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await events_channel.send(content=get_game_role_mention(), embed=notification_embed)
        except GameNotFoundError:
            await ctx.respond("❌ | Игра не выбрана.", ephemeral=True)

    @slash_command(
        name="close_game_registration",
        description="Закрыть регистрацию на текущую игру для новых игроков"
    )
    async def close_game_registration(self, ctx: ApplicationContext) -> None:
        try:
            if not verify_admin(ctx):
                return

            await games_core.close_registration_for_current_game()
            await ctx.respond("✅ | Регистрация на игру закрыта.", ephemeral=True)

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)
            notification_embed = Embed(
                title="[🔧] Техническое уведомление",
                color=EmbedColors.RED,
                description=f"Регистрация на текущую игру была закрыта"
            )
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await events_channel.send(content=get_game_role_mention(), embed=notification_embed)
        except GameNotFoundError:
            await ctx.respond("❌ | Игра не выбрана.", ephemeral=True)

    @slash_command(
        name="game_session",
        description="Открыть настройки игровой сессии"
    )
    async def show_game_session_status(self, ctx: ApplicationContext) -> None:
        if config_class.data.game_session_is_open:
            await ctx.respond("✅ | Игровая сессия включена", view=GameSessionView())
        else:
            await ctx.respond("❌ | Игровая сессия выключена", view=GameSessionView())

    @slash_command(
        name="finish_game",
        description="Завершает текущую игру"
    )
    async def finish_current_game(
        self,
        ctx: ApplicationContext,
        winner_1: Member = Option(Member, required=True),
        winner_2: Member = Option(Member, required=False),
        winner_3: Member = Option(Member, required=False),
        image_link: str = Option(str, required=False)
    ) -> None:
        if not await verify_admin(ctx):
            return

        if winner_2 and winner_3:
            winners = [winner_1.id, winner_2.id, winner_3.id]
        elif winner_2 and not winner_3:
            winners = [winner_1.id, winner_2.id]
        elif not winner_2 and winner_3:
            winners = [winner_1.id, winner_3.id]
        else:
            winners = [winner_1.id]

        winners_str = [f"<@{winner_id}>" for winner_id in winners]

        try:
            await games_core.finish_current_game(winners, image_link)
            await ctx.respond("Игра была завершена.")

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)
            notification_embed = Embed(
                title="[🔧] Техническое уведомление",
                color=EmbedColors.GREEN,
                description=f"Игра была завершена!\nПобедители: {" ".join(winners_str)}"
            )

            try:
                notification_embed.set_image(url=image_link)
            except Exception as e:
                print(e)

            await events_channel.send(content=get_game_role_mention(), embed=notification_embed)

        except GameNotFoundError:
            await ctx.respond("❌ | Игра не выбрана.", ephemeral=True)

    @slash_command(
        name="select_game",
        description="Выбрать игру, к которой будут применяться остальные команды"
    )
    async def select_game(self, ctx: ApplicationContext, game_id: int) -> None:
        try:
            if not await verify_admin(ctx):
                return

            await games_core.select_game(game_id)

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)
            notification_embed = Embed(
                title="[🔧] Техническое уведомление",
                color=EmbedColors.GREEN,
                description=f"Игра c ID {game_id} была выбрана и теперь является текущей игрой"
            )

            await ctx.respond(f"✅ | Игра с ID {game_id} выбрана.", ephemeral=True)
            await events_channel.send(embed=notification_embed)

        except GameNotFoundError:
            await ctx.respond("❌ | Игра не найдена. Убедитесь, что был введён верный ID.", ephemeral=True)
        except GameSessionIsNotClosedError:
            await ctx.respond(
                "❌ | Вы не можете переключиться на другую игру, не завершив текущую игровую сессию.",
                ephemeral=True
            )

    @slash_command(
        name="delete_game",
        description="Удалить текущую (выбранную) игру"
    )
    async def delete_current_game(self, ctx: ApplicationContext) -> None:
        if not await verify_admin(ctx):
            return

        await ctx.respond(
            "Вы уверены, что хотите удалить текущую игру? Это необратимое действие",
            view=GameDeleteView(),
            ephemeral=True
        )


def setup(bot: Bot):
    bot.add_cog(Games(bot))
