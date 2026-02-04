from discord.ext.commands import Cog, Bot, slash_command
from discord import Member, ApplicationContext, Embed

from app.discord_api.embed_colors import EmbedColors
from app.sql_api.core.exceptions.games import GameSessionIsClosedError
from app.sql_api.sql.core.exceptions.players import PlayerNotFoundError, PlayerIsEliminatedError
from app.sql_api.sql.core.exceptions.wars import AlreadyInWarError, PlayerWarLimitError, WarCooldownNotFinishedError

from app.utils.config import config_class

from app.discord_api.other import wars_core, players_core, get_admin_mentions, verify_admin

from app.discord_api.views.wars import ReviveRequestView, OfferTruceView


class Wars(Cog):
    @slash_command(
        name="declare_war",
        description="Объявить войну другому игроку"
    )
    async def declare_war(self, ctx: ApplicationContext, player: Member) -> None:
        if ctx.user.id == player.id:
            await ctx.respond("❌ | Вы не можете объявить войну самому себе.", ephemeral=True)

            return

        try:
            await wars_core.declare_war(ctx.user.id, player.id)

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)

            notification_embed = Embed(
                color=EmbedColors.CHEESE,
                description=f"Игрок {ctx.user.mention} объявил войну игроку {player.mention}"
            )
            notification_embed.set_author(name="[⚔️] Новая война", icon_url=ctx.user.avatar.url)
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await ctx.respond(f"⚔️ | Вы объявили войну игроку {player.mention}", ephemeral=True),
            await events_channel.send(
                content=f"||{player.mention}||" + "\n" + get_admin_mentions(),
                embed=notification_embed
            )
        except AlreadyInWarError:
            await ctx.respond("❌ | Вы уже находитесь в состоянии войны и не можете начать новую.", ephemeral=True)
        except WarCooldownNotFinishedError:
            await ctx.respond("❌ | Вы не можете объявить войну до окончания 30-минутного кулдауна.", ephemeral=True)
        except PlayerWarLimitError:
            await ctx.respond("❌ | Игрок, которому вы пытаетесь объявить войну, уже находится в 3 войнах.", ephemeral=True)
        except PlayerNotFoundError:
            await ctx.respond(
                "❌ | Не удалось объявить войну игроку. Игрок либо не участвует в игре, либо вы сами не участвуете в игре.",
                ephemeral=True
            )
        except PlayerIsEliminatedError:
            await ctx.respond(
                "❌ | Не удалось объявить войну игроку. Выбыли либо вы, либо игрок, которому вы объявляете войну.",
                ephemeral=True
            )
        except GameSessionIsClosedError:
            await ctx.respond("❌ | Вы не можете совершать игровые действия вне игровой сессии.", ephemeral=True)

    @slash_command(
        name="offer_truce",
        description="Предложить перемирие игроку"
    )
    async def offer_truce(self, ctx: ApplicationContext, enemy: Member) -> None:
        try:
            player_wars = (await players_core.get_player(ctx.user.id)).wars.wars

            if not config_class.data.game_session_is_open:
                await ctx.respond("❌ | Вы не можете совершать игровые действия вне игровой сессии.", ephemeral=True)

                return

            if not any([enemy.id in (war.defender, war.aggressor) for war in player_wars]):
                await ctx.respond("❌ | Вы не находитесь в состоянии войны с этим игроком.", ephemeral=True)

                return

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)

            notification_embed = Embed(
                color=EmbedColors.CHEESE,
                description=f"Игрок {ctx.user.mention} предлагает игроку {enemy.mention} заключить перемирие."
            )
            notification_embed.set_author(name="[🤝] Предложение о перемирии", icon_url=ctx.user.avatar.url)
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await events_channel.send(content=enemy.mention, embed=notification_embed, view=OfferTruceView())
        except PlayerNotFoundError:
            await ctx.respond("❌ | Один из игроков не был найден в базе данных: вероятно, он был указан неверно.")

    @slash_command(
        name="eliminate_player",
        description="Устранить игрока после полного поражения в войне",
    )
    async def eliminate_player(self, ctx: ApplicationContext, player: Member):
        try:
            if not await verify_admin(ctx):
                return

            await wars_core.eliminate_player(player.id)

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)

            notification_embed = Embed(
                color=EmbedColors.RED,
                description=f"Игрок {player.mention} выбыл."
            )
            notification_embed.set_author(name="[💀] Игрок выбыл", icon_url=player.avatar.url)
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await ctx.respond("✅ | Игрок выбыл.", ephemeral=True)
            await events_channel.send(embed=notification_embed)
        except PlayerIsEliminatedError:
            await ctx.respond("❌ | Игрок уже выбыл.", ephemeral=True)
        except PlayerNotFoundError:
            await ctx.respond("❌ | Игрок не был найден в базе данных.", ephemeral=True)
        except GameSessionIsClosedError:
            await ctx.respond("❌ | Вы не можете совершать игровые действия вне игровой сессии.", ephemeral=True)

    @slash_command(
        name="request_to_revive_player",
        description="Попросить отдать выбывшему игроку часть своей территории, чтобы возродить его."
    )
    async def request_to_revive_player(
        self,
        ctx: ApplicationContext,
        player_to_revive: Member,
        description: str
    ) -> None:
        try:
            reviver = await players_core.get_player(ctx.user.id)
            revived = await players_core.get_player(player_to_revive.id)

            if reviver.is_eliminated:
                await ctx.respond(
                    "❌ | Вы не можете отправить запрос на возрождение данного игрока, поскольку вы выбыли из игры",
                    ephemeral=True
                )

                return

            if not revived.is_eliminated:
                await ctx.respond(
                    "❌ | Вы не можете отправить запрос на возрождение данного игрока, поскольку он не выбывал из игры",
                    ephemeral=True
                )

                return

            if not config_class.data.game_session_is_open:
                await ctx.respond("❌ | Вы не можете совершать игровые действия вне игровой сессии.", ephemeral=True)

                return

            events_channel = ctx.bot.get_channel(config_class.data.events_chat_id)

            notification_embed = Embed(
                color=EmbedColors.CHEESE,
                description=f"Игрок {ctx.user.mention} запрашивает возрождение игрока {player_to_revive.mention} за счёт своей территории"
            )
            notification_embed.set_author(name="[♻️️] Запрос на возрождение игрока", icon_url=ctx.user.avatar.url)
            notification_embed.add_field(name="Комментарий", value=description)
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await ctx.respond("✅ | Запрос на возрождение игрока был отправлен.", ephemeral=True)
            await events_channel.send(
                f"||<@725527674717732894>||",
                embed=notification_embed,
                view=ReviveRequestView()
            )
        except PlayerNotFoundError:
            await ctx.respond(
                "❌ | Вы не можете отправить запрос на возрождение данного игрока, кто-то из вас не участвует в игре",
                ephemeral=True
            )


def setup(bot: Bot):
    bot.add_cog(Wars(bot))
