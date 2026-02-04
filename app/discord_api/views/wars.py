from discord import ButtonStyle, Embed, Interaction
from discord.ui import View, button, Button

from app.discord_api.other import verify_admin, wars_core, get_admin_mentions

from app.discord_api.embed_colors import EmbedColors


class OfferTruceView(View):
    @button(label="Принять", style=ButtonStyle.success)
    async def accept_revive_button(self, butt: Button, interaction: Interaction) -> None:
        players_parsed = interaction.message.embeds[0].description.replace("@", "").replace("<", "|").replace(">", "|").split("|")

        player_id = int(players_parsed[1])
        enemy_id = int(players_parsed[3])

        if enemy_id != interaction.user.id:
            await interaction.respond("Не тебе, олух.", ephemeral=True)

            return

        embed = interaction.message.embeds[0].copy()
        embed.colour = EmbedColors.GREEN
        embed.add_field(name="Ответ", value="🤝 | Перемирие заключено")

        self.stop()

        await wars_core.make_truce(player_id, enemy_id)
        await interaction.message.edit(embed=embed)
        await interaction.message.reply(get_admin_mentions())
        await interaction.response.edit_message(view=self)

    @button(label="Отклонить", style=ButtonStyle.danger)
    async def decline_revive_button(self, butt: Button, interaction: Interaction) -> None:
        if int(interaction.message.content[2:-1]) != interaction.user.id:
            await interaction.respond("Не тебе, олух.", ephemeral=True)

        embed = interaction.message.embeds[0].copy()

        embed.colour = EmbedColors.RED
        embed.add_field(name="Ответ", value="❌ | Предложение отклонено")

        self.stop()

        await interaction.message.edit(embed=embed)
        await interaction.response.edit_message(view=self)


class ReviveRequestView(View):
    @button(label="Принять", style=ButtonStyle.success)
    async def accept_revive_button(self, butt: Button, interaction: Interaction) -> None:
        if not await verify_admin(interaction):
            return

        player_to_revive_id = int(interaction.message.embeds[0].description.replace("@", "").replace("<", "|").replace(">", "|").split("|")[-2])
        player_to_revive = interaction.guild.get_member(player_to_revive_id)

        embed = interaction.message.embeds[0].copy()
        embed.colour = EmbedColors.GREEN
        embed.add_field(name="Ответ хоста", value="✅ | Запрос принят")

        revive_embed = Embed(color=EmbedColors.GREEN, description=f"Игрок {player_to_revive.mention} был возрождён")
        revive_embed.set_author(name="[🚩] Уведомление о возрождении игрока", icon_url=player_to_revive.avatar.url)

        self.stop()

        await wars_core.revive_player(player_to_revive_id)
        await interaction.message.edit(embed=embed)
        await interaction.channel.send(content=get_admin_mentions(), embed=revive_embed)
        await interaction.response.edit_message(view=self)

    @button(label="Отклонить", style=ButtonStyle.danger)
    async def decline_revive_button(self, butt: Button, interaction: Interaction) -> None:
        if not await verify_admin(interaction):
            return

        embed = interaction.message.embeds[0].copy()

        embed.colour = EmbedColors.RED
        embed.add_field(name="Ответ хоста", value="❌ | Запрос отклонён")

        self.stop()

        await interaction.message.edit(embed=embed)
        await interaction.response.edit_message(view=self)
