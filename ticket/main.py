import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Suporte",
                description="Abrir ticket para suporte",
                emoji="🛠️"
            ),
            discord.SelectOption(
                label="Compra",
                description="Abrir ticket para comprar algo",
                emoji="🛒"
            ),
            discord.SelectOption(
                label="Denúncia",
                description="Abrir ticket para denúncia",
                emoji="🚨"
            ),
        ]

        super().__init__(
            placeholder="Selecione o motivo do ticket...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        motivo = self.values[0]

        existing_channel = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{user.id}"
        )

        if existing_channel:
            await interaction.response.send_message(
                f"❌ Você já possui um ticket aberto: {existing_channel.mention}",
                ephemeral=True
            )
            return

        categoria = discord.utils.get(guild.categories, name="Tickets")

        if categoria is None:
            categoria = await guild.create_category("Tickets")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                read_message_history=True
            )
        }

        # Dá acesso para cargos com permissão de administrador
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True
                )

        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            category=categoria,
            overwrites=overwrites,
            topic=f"Ticket de {user} | Motivo: {motivo}"
        )

        embed = discord.Embed(
            title="🎫 Ticket Aberto",
            description=(
                f"Olá {user.mention}, seu ticket foi criado.\n\n"
                f"**Motivo:** {motivo}\n\n"
                "Aguarde um membro da equipe responder."
            ),
            color=discord.Color.green()
        )

        await channel.send(
            content=user.mention,
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            f"✅ Seu ticket foi criado: {channel.mention}",
            ephemeral=True
        )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="close_ticket"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        member = interaction.user

        if not member.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "❌ Apenas a equipe pode fechar este ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Ticket será fechado em alguns segundos..."
        )

        await interaction.channel.delete()


@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())

    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)

    print(f"Bot conectado como {bot.user}")


@bot.tree.command(
    name="ticket",
    description="Envia o painel de tickets",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.default_permissions(administrator=True)
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Sistema de Tickets",
        description="Selecione abaixo o motivo para abrir um ticket.",
        color=discord.Color.green()
    )

    await interaction.response.send_message(
        embed=embed,
        view=TicketView()
    )


bot.run(TOKEN)
