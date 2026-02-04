from discord import ButtonStyle, Embed, Interaction
from discord.ui import View, button, Button

from app.discord_api.embed_colors import EmbedColors
from app.sql_api.core.exceptions.games import GameSessionIsNotClosedError, GameSessionIsClosedError
from app.discord_api.other import verify_admin, games_core, wars_core, researches_core
from app.sql_api.sql.core.exceptions.games import GameNotFoundError

from app.utils.config import config_class
from app.discord_api.other import technology_production_tasks, get_game_role_mention


class CurrentGameView(View):
    pass


class GameDeleteView(View):
    @button(label="Да", style=ButtonStyle.success)
    async def delete_game(self, butt: Button, interaction: Interaction) -> None:
        try:
            current_game_id = config_class.data.current_game_id

            events_channel = interaction.client.get_channel(config_class.data.events_chat_id)
            notification_embed = Embed(
                title="[🔧] Техническое уведомление",
                color=EmbedColors.RED,
                description=f"Игра с ID {current_game_id} была удалена"
            )

            await games_core.delete_current_game()
            await interaction.respond("✅ | Игра была удалена из базы данных.", ephemeral=True)
            await events_channel.send(embed=notification_embed)
        except GameNotFoundError:
            await interaction.respond("❌ | Игра не выбрана.", ephemeral=True)

        self.stop()

    @button(label="Нет", style=ButtonStyle.danger)
    async def cancel_game_delete(self, butt: Button, interaction: Interaction) -> None:
        self.stop()

        await interaction.response.edit_message(view=self)


class GameSessionView(View):
    @button(label="Запустить", style=ButtonStyle.success)
    async def open_game_session(self, butt: Button, interaction: Interaction) -> None:
        if not await verify_admin(interaction):
            return

        try:
            await games_core.start_game_session()

            events_channel = interaction.client.get_channel(config_class.data.events_chat_id)
            notification_embed = Embed(
                title="[🔧] Техническое уведомление",
                color=EmbedColors.GREEN,
                description=f"Игровая сессия для текущей игры была запущена"
            )
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await interaction.message.edit(content="✅ | Игровая сессия включена")
            await events_channel.send(content=get_game_role_mention(), embed=notification_embed)
            await interaction.response.edit_message(view=self)

            await researches_core.continue_delayed_players_researches()
            await wars_core.toggle_war_cooldowns()
            await researches_core.continue_delayed_players_item_productions()

        except GameNotFoundError:
            await interaction.respond("❌ | Игра не выбрана.", ephemeral=True)
        except GameSessionIsNotClosedError:
            await interaction.respond("❌ | Игровая сессия уже запущена.", ephemeral=True)

    @button(label="Завершить", style=ButtonStyle.danger)
    async def close_game_session(self, butt: Button, interaction: Interaction) -> None:
        if not await verify_admin(interaction):
            return

        try:
            await games_core.close_game_session()

            events_channel = interaction.client.get_channel(config_class.data.events_chat_id)
            notification_embed = Embed(
                title="[🔧] Техническое уведомление",
                color=EmbedColors.RED,
                description=f"Игровая сессия для текущей игры была закрыта"
            )
            notification_embed.set_footer(text=f"ID игры: {config_class.data.current_game_id}")

            await interaction.message.edit(content="❌ | Игровая сессия выключена")
            await events_channel.send(content=get_game_role_mention(), embed=notification_embed)
            await interaction.response.edit_message(view=self)

            await researches_core.delay_players_current_researches()
            await wars_core.toggle_war_cooldowns()
            await researches_core.delay_players_current_item_productions()

            for task in technology_production_tasks:
                task.close()

        except GameNotFoundError:
            await interaction.respond("❌ | Игра не выбрана.", ephemeral=True)
        except GameSessionIsClosedError:
            await interaction.respond("❌ | Игровая сессия уже завершена.", ephemeral=True)
