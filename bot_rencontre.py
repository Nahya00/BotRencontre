import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1361778893681463436  # Remplace par ton ID de serveur
CHANNEL_ACCUEIL = 1379271057520721961
CHANNEL_FILLE = 1379271062012821515
CHANNEL_GARCON = 1379271067369082940
CHANNEL_LOGS = 1379271457187696711

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

profils = {}

class StartProfilButton(Button):
    def __init__(self):
        super().__init__(label="Remplir mon profil", style=discord.ButtonStyle.primary, custom_id="start_profil")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=False, ephemeral=True)
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
            ("Genre ? (Garçon / Fille)", "Genre"),
            ("Orientation ? (Hétéro / Bi / Homo / Autre)", "Orientation"),
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
        await channel.send("✅ Ton profil a bien été publié dans le serveur !")
        await poster_profil(interaction, profil_data, image_url)

class StartProfilView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StartProfilButton())

class ProfilView(View):
    def __init__(self, auteur_id):
        super().__init__(timeout=None)
        self.auteur_id = auteur_id
      


    @discord.ui.button(label="Contacter cette personne", style=discord.ButtonStyle.success)
    async def contact(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        auteur = await bot.fetch_user(self.auteur_id)
        if auteur:
            try:
                data1 = profils.get(interaction.user.id)
                data2 = profils.get(self.auteur_id)
                if data1 and data2:
                    age1 = int(data1.get("Âge", 0))
                    age2 = int(data2.get("Âge", 0))
                    age_limit = (age2 / 2) + 7
                    if age1 < age_limit:
                        await interaction.user.send("⛔ Tu ne peux pas contacter cette personne.\nL’écart d’âge est jugé inapproprié selon la règle du ‘théorème du pointeur’. Merci de respecter autrui.")
                        return
                await interaction.user.send(f"📬 Tu as demandé à contacter {auteur.mention}.")
                await auteur.send(f"📬 {interaction.user.mention} souhaite te contacter ! Voici son profil :")
                if profils.get(interaction.user.id):
                    await auteur.send(embed=build_profile_embed(interaction.user, profils[interaction.user.id], interaction.user.avatar.url))
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

def build_profile_embed(user, data, image_url):
    genre = data.get("Genre", "").lower()
    color = discord.Color.dark_magenta() if "fille" in genre else discord.Color.dark_blue()
    titre = "💖 Nouveau profil Fille !" if "fille" in genre else "💙 Nouveau profil Garçon !"
    embed = discord.Embed(title=titre, description="❖ Un nouveau profil vient d'apparaître...\n\n> Il y a des regards qui racontent plus que mille mots.", color=color)
    for champ in ["Prénom", "Âge", "Département", "Genre", "Orientation", "Recherche", "Recherche chez quelqu'un", "Passions", "Description"]:
        embed.add_field(name=champ, value=data.get(champ, "?"), inline=False)
    embed.set_footer(text="Tsukaya - Profil mystère")
    embed.set_thumbnail(url=image_url)
    embed.set_author(name=user.name, icon_url=user.avatar.url if user.avatar else None)
    return embed

async def poster_profil(interaction, data, image_url):
    genre = data.get("Genre", "").lower()
    target_channel = bot.get_channel(CHANNEL_FILLE) if "fille" in genre else bot.get_channel(CHANNEL_GARCON)
    embed = build_profile_embed(interaction.user, data, image_url)
    if target_channel:
        message = await target_channel.send(embed=embed, view=ProfilView(interaction.user.id))
        await message.add_reaction("✅")
        await message.add_reaction("❌")

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
            title="Rencontre Mystère Tsukaya",
            description="**Clique ci-dessous pour créer ton profil.**\nLes regards ne mentent jamais...",
            color=discord.Color.from_rgb(20, 20, 20)
        )
        embed.set_footer(text="Tsukaya")
        embed.set_author(name="Système de Rencontre", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await accueil_channel.send(embed=embed, view=StartProfilView())

bot.run(TOKEN)


