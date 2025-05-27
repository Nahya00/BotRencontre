import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1360356060229013605  # Remplace par ton ID de serveur
CHANNEL_ACCUEIL = 1362035171301527654
CHANNEL_FILLE = 1362035175269077174
CHANNEL_GARCON = 1362035179358781480
CHANNEL_LOGS = 1376347435747643475

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

profils = {}

class StartProfilButton(Button):
    def __init__(self):
        super().__init__(label="Remplir mon profil", style=discord.ButtonStyle.primary, custom_id="start_profil")

    async def callback(self, interaction: discord.Interaction):
        channel = await interaction.user.create_dm()
        await channel.send("Salut ! On va remplir ta présentation.\nEnvoie une image ou un lien, ou écris `skip`.")

        def check(m):
            return m.author.id == interaction.user.id and isinstance(m.channel, discord.DMChannel)

        try:
            msg = await bot.wait_for("message", check=check, timeout=120)
            if msg.attachments:
                image_url = msg.attachments[0].url
            elif msg.content.startswith("http"):
                image_url = msg.content.strip()
            elif msg.content.lower() == "skip":
                image_url = interaction.user.avatar.url if interaction.user.avatar else None
            else:
                await channel.send("❌ Envoie un lien ou une image, ou écris `skip`.")
                return
        except Exception:
            await channel.send("❌ Une erreur est survenue.")
            return

        questions = [
            ("Quel est ton prénom ?", "Prénom"),
            ("Ton âge (15-35) ?", "Âge"),
            ("Département ?", "Département"),
            ("Genre ? (Garçon / Fille )", "Genre"),
            ("Orientation ?", "Orientation"),
            ("Que recherches-tu sur ce serveur ?", "Recherche"),
            ("Qu'attends-tu chez quelqu'un ?", "Recherche chez quelqu'un"),
            ("Tes passions ?", "Passions"),
            ("Petite description :", "Description")
        ]

        profil_data = {}

        for question, key in questions:
            await channel.send(question)
            try:
                answer = await bot.wait_for("message", check=check, timeout=120)
                value = answer.content.strip()
                if key == "Âge":
                    if not value.isdigit():
                        await channel.send("Merci d'indiquer un âge valide.")
                        return
                    age = int(value)
                    if age < 15 or age > 35:
                        await channel.send("Âge invalide. Réessaie entre 15 et 35.")
                        return
                profil_data[key] = value
            except:
                await channel.send("⛔ Temps dépassé ou erreur.")
                return

        profils[interaction.user.id] = profil_data
        await poster_profil(interaction, profil_data, image_url)

class StartProfilView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StartProfilButton())

class ProfilView(View):
    def __init__(self, auteur_id):
        super().__init__(timeout=None)
        self.auteur_id = auteur_id

    async def interaction_check(self, interaction: discord.Interaction):
        return True

    @discord.ui.button(label="Contacter cette personne", style=discord.ButtonStyle.success)
    async def contact(self, interaction: discord.Interaction, button: discord.ui.Button):
        auteur = await bot.fetch_user(self.auteur_id)
        if auteur:
            try:
                await interaction.user.send(f"📬 Tu as demandé à contacter {auteur.mention}.")
                await auteur.send(f"📬 {interaction.user.mention} souhaite te contacter !")
            except:
                pass

        logs = bot.get_channel(CHANNEL_LOGS)
        if logs:
            await logs.send(f"📨 {interaction.user} a cliqué sur le bouton de contact du profil de {auteur} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    @discord.ui.button(label="Signaler ce profil", style=discord.ButtonStyle.danger)
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚠️ Le profil a été signalé. Merci pour ton retour.", ephemeral=True)
        logs = bot.get_channel(CHANNEL_LOGS)
        if logs:
            await logs.send(f"🚨 {interaction.user} a signalé un profil ({self.auteur_id}) à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

async def poster_profil(interaction, data, image_url):
    genre = data.get("Genre", "").lower()
    if "fille" in genre:
        target_channel = bot.get_channel(CHANNEL_FILLE)
        color = discord.Color.dark_magenta()
        titre = "💖 Nouveau profil Fille !"
    else:
        target_channel = bot.get_channel(CHANNEL_GARCON)
        color = discord.Color.dark_blue()
        titre = "💙 Nouveau profil Garçon !"

    embed = discord.Embed(title=titre, description="❖ Un nouveau profil vient d'apparaître...\n\n> Il y a des regards qui racontent plus que mille mots.", color=color)
    for champ in ["Prénom", "Âge", "Département", "Genre", "Orientation", "Recherche", "Recherche chez quelqu'un", "Passions", "Description"]:
        embed.add_field(name=champ, value=data.get(champ, "?"), inline=False)
    embed.set_footer(text="Noctys - Profil mystère")
    embed.set_thumbnail(url=image_url)
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

    if target_channel:
        message = await target_channel.send(embed=embed, view=ProfilView(interaction.user.id))

    logs = bot.get_channel(CHANNEL_LOGS)
    if logs:
        await logs.send(f"🧾 Profil de {interaction.user} posté dans {'fille' if 'fille' in genre else 'garçon'} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    accueil_channel = bot.get_channel(CHANNEL_ACCUEIL)
    if accueil_channel:
        try:
            await accueil_channel.purge(limit=5)
        except:
            pass
        embed = discord.Embed(
            title="Rencontre Mystère Noctys",
            description="**Clique ci-dessous pour créer ton profil anonyme.**\nLes regards ne mentent jamais...",
            color=discord.Color.from_rgb(20, 20, 20)
        )
        embed.set_footer(text=".gg/noctys")
        embed.set_author(name="Système de Rencontre", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await accueil_channel.send(embed=embed, view=StartProfilView())

bot.run(TOKEN)

