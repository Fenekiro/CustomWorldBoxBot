import time

from discord.ext.commands import Cog, Bot, slash_command
from discord import ApplicationContext, Embed, Option, Member

from app.discord_api.embed_colors import EmbedColors
from app.discord_api.other import verify_commands_channel, players_core

from app.sql_api.core.types.players import PlayerRegisterData
from app.sql_api.sql.core.exceptions.games import GameNotFoundError
from app.sql_api.sql.core.exceptions.players import PlayerAlreadyRegisteredError, GameRegistrationIsClosedError, PlayerNotFoundError

from app.utils.config import config_class


class Players(Cog):
    @slash_command(
        name="current_game_players",
        description="Показать всех игроков текущей игры"
    )
    async def current_game_players(self, ctx: ApplicationContext) -> None:
        if not await verify_commands_channel(ctx):
            return

        players_discord_ids = [player.discord_id for player in await players_core.get_players()]
        players_embed = Embed(
            title=f"Участники текущей игры",
            description="\n".join([f"<@{discord_id}>" for discord_id in players_discord_ids]),
            color=EmbedColors.CHEESE
        )
        players_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

        await ctx.respond(embed=players_embed)

    @slash_command(
        name="register_for_game",
        description="Зарегистрироваться на игру в качестве участника"
    )
    async def register_player(
        self,
        ctx: ApplicationContext,
        country_name: str,
        capital_name: str,
        race: str = Option(str, choices=["Люди", "Дварфы", "Эльфы", "Орки"]),
        country_color: str = Option(str, required=False)
    ) -> None:
        if not await verify_commands_channel(ctx):
            return

        races_translate = {"Люди": "Human", "Дварфы": "Dwarf", "Эльфы": "Elf", "Орки": "Ork"}

        register_data = PlayerRegisterData(
            ctx.user.id,
            str(),
            country_name,
            capital_name,
            races_translate[race],
            "Deprecated"
        )

        players_registration_channel = ctx.bot.get_channel(config_class.data.registration_for_game_chat_id)

        notification_embed = Embed(color=EmbedColors.GREEN)
        notification_embed.set_author(
            name=f"[➕] Регистрация игрока {ctx.user.display_name}",
            icon_url=ctx.user.avatar.url
        )
        notification_embed.add_field(name="1. Название страны", value=country_name)
        notification_embed.add_field(name="2. Название столицы", value=capital_name)
        notification_embed.add_field(name="3. Раса", value=race)
        notification_embed.add_field(name="4. Цвет страны", value=country_color)
        notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

        registration_message = await players_registration_channel.send(embed=notification_embed)

        try:
            register_data.registration_message_discord_id = str(registration_message.id)

            await players_core.register_player(register_data)
            await ctx.respond("✅ | Вы успешно зарегистрировались!", ephemeral=True)
        except PlayerAlreadyRegisteredError:
            await registration_message.delete()
            await ctx.respond("❌ | Вы уже зарегистрировались.", ephemeral=True)
        except GameRegistrationIsClosedError:
            await registration_message.delete()
            await ctx.respond(
                "❌ | Вы не можете зарегистрироваться на игру, поскольку регистрация на неё уже закрыта.",
                ephemeral=True
            )
        except GameNotFoundError:
            await registration_message.delete()
            await ctx.respond("❌ | Текущая игра не выбрана, регистрация невозможна.", ephemeral=True)

    @slash_command(
        name="player_profile",
        description="Показать профиль игрока в текущей игре"
    )
    async def player_profile(
        self,
        ctx: ApplicationContext,
        player: Member = Option(Member, required=False)
    ) -> None:
        if not await verify_commands_channel(ctx):
            return

        try:
            if player:
                player_data = await players_core.get_player(player.id)
            else:
                player = ctx.user
                player_data = await players_core.get_player(ctx.user.id)

            is_alive = "✅" if not player_data.is_eliminated else "💀"
            player_enemies = []
            war_cooldown = player_data.wars.cant_declare_war_until_timestamp

            if player_data.race == "Human":
                race = "Люди"
            elif player_data.race == "Dwarf":
                race = "Дварфы"
            elif player_data.race == "Ork":
                race = "Орки"
            else:
                race = "Эльфы"

            if war_cooldown is not None and war_cooldown > 100_000:
                war_cooldown -= time.time()

                if war_cooldown < 0:
                    war_cooldown_str = "⚔️"
                else:
                    war_cooldown_str = time.strftime("%M:%S", time.gmtime(war_cooldown))
            elif war_cooldown is not None and war_cooldown < 100_000:
                war_cooldown_str = time.strftime("%M:%S", time.gmtime(war_cooldown))
            else:
                war_cooldown_str = "⚔️"

            for war in player_data.wars.wars:
                if war.aggressor == player_data.discord_id:
                    player_enemies.append(war.defender)
                else:
                    player_enemies.append(war.aggressor)

            player_enemies = "\n".join([f"<@{enemy_discord_id}>" for enemy_discord_id in player_enemies])

            player_embed = Embed(color=EmbedColors.CHEESE)
            player_embed.set_author(
                name=f"Игровой профиль игрока {player.display_name}",
                icon_url=player.avatar
            )
            player_embed.add_field(name="Название государства", value=player_data.country_name)
            player_embed.add_field(name="Название столицы", value=player_data.capital_name)
            player_embed.add_field(name="Раса", value=race)
            player_embed.add_field(name="Жив?", value=is_alive)
            player_embed.add_field(name="В войне с:", value=player_enemies)
            player_embed.add_field(name="Кулдаун войны", value=war_cooldown_str)
            player_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await ctx.respond(embed=player_embed)
        except PlayerNotFoundError:
            await ctx.respond(f"Игрок {player.mention} не был найден в базе данных.", ephemeral=True)

    @slash_command(
        name="cancel_player_registration",
        description="Отменить вашу заявку на участие в игре"
    )
    async def cancel_player_registration(self, ctx: ApplicationContext) -> None:
        if not await verify_commands_channel(ctx):
            return

        try:
            player = await players_core.get_player(ctx.user.id)

            await players_core.delete_player(ctx.user.id)
            await ctx.respond("✅ | Вы отменили свою регистрацию на игру.", ephemeral=True)

            registration_message = ctx.bot.get_message(int(player.registration_message_discord_id))

            await registration_message.delete()

        except PlayerNotFoundError:
            await ctx.respond("❌ | Вы не были зарегистрированы на текущую игру.", ephemeral=True)
        except GameRegistrationIsClosedError:
            await ctx.respond("❌ | Вы не можете отменить регистрацию на игру, если она уже началась.", ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(Players(bot))
