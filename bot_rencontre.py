import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
import asyncio
import random
import os

TOKEN = "TON_TOKEN_ICI"
GUILD_ID = 123456789012345678
CHANNEL_ACCUEIL = 123456789012345678
CHANNEL_FILLE = 123456789012345678
CHANNEL_GARCON = 123456789012345678
CHANNEL_LOGS = 123456789012345678

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
profils = {}

class ProfilView(View):
    def __init__(self, auteur_id):
        super().__init__(timeout=None)
        self.auteur_id = auteur_id

    @discord.ui.button(label="Contacter cette personne", style=discord.ButtonStyle.success, custom_id="contact_button")
    async def contact(self, interaction: discord.Interaction, button: discord.ui.Button):
        cible_id = int(interaction.message.embeds[0].footer.text.split("Profil ID: ")[1])
        if cible_id == interaction.user.id:
            await interaction.response.send_message("❌ Tu ne peux pas te contacter toi-même.", ephemeral=True)
            return

        auteur_profil = profils.get(cible_id)
        cible_profil = profils.get(interaction.user.id)
        age1 = int(auteur_profil["Âge"])
        age2 = int(cible_profil["Âge"]) if cible_profil else None
        compatible = calcul_compatibilite(age1, age2)

        message = f"📩 {interaction.user} a cliqué sur le bouton de contact du profil de {auteur_profil['Prénom']}#{cible_id} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        if compatible == 0:
            message += " | Compatibilité : 0% ⚠️ (Faible compatibilité)"
        elif compatible >= 90:
            message += f" | Compatibilité : {compatible}% ✅ Très bonne compatibilité"
        else:
            message += f" | Compatibilité : {compatible}% ⚠️"

        logs_channel = bot.get_channel(CHANNEL_LOGS)
        await logs_channel.send(message)

        try:
            user = await bot.fetch_user(cible_id)
            await user.send(f"{interaction.user.name}#{interaction.user.discriminator} a voulu te contacter via ton profil.")
        except:
            pass

        await interaction.response.send_message("✅ La demande a été envoyée !", ephemeral=True)

    @discord.ui.button(label="Signaler ce profil", style=discord.ButtonStyle.danger, custom_id="report_button")
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        cible_id = int(interaction.message.embeds[0].footer.text.split("Profil ID: ")[1])
        await interaction.response.send_message("🚨 Le profil a été signalé à la modération.", ephemeral=True)
        logs_channel = bot.get_channel(CHANNEL_LOGS)
        await logs_channel.send(f"🚨 {interaction.user.name}#{interaction.user.discriminator} a signalé le profil de {cible_id} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}.")

@bot.tree.command(name="start", description="Créer ton profil")
async def start(interaction: discord.Interaction):
    await interaction.response.send_message("Salut ! On va remplir ta présentation en DM.", ephemeral=True)
    try:
        user = await bot.fetch_user(interaction.user.id)
        await creer_profil(user, interaction)
    except:
        await interaction.followup.send("Impossible de t’envoyer un DM. Active-les.", ephemeral=True)

async def creer_profil(user, interaction):
    def check(m):
        return m.author.id == user.id and isinstance(m.channel, discord.DMChannel)

    await user.send("Envoie une image ou un lien, ou écris `skip`.")
    try:
        msg = await bot.wait_for("message", check=check, timeout=120)
        if msg.attachments:
            image_url = msg.attachments[0].url
        elif msg.content.startswith("http"):
            image_url = msg.content.strip()
        elif msg.content.lower() == "skip":
            image_url = user.avatar.url if user.avatar else None
        else:
            await user.send("❌ Envoie un lien ou une image, ou écris `skip`.")
            return
    except:
        await user.send("❌ Temps dépassé ou erreur.")
        return

    questions = [
        ("Quel est ton prénom ?", "Prénom"),
        ("Ton âge (15-35) ?", "Âge"),
        ("Département ?", "Département"),
        ("Genre ? (Garçon / Fille / Autre)", "Genre"),
        ("Orientation ?", "Orientation"),
        ("Que recherches-tu sur ce serveur ?", "Recherche"),
        ("Qu'attends-tu chez quelqu'un ?", "Recherche chez quelqu'un"),
        ("Tes passions ?", "Passions"),
        ("Petite description :", "Description")
    ]

    profil_data = {}
    for question, key in questions:
        await user.send(question)
        try:
            answer = await bot.wait_for("message", check=check, timeout=120)
            value = answer.content.strip()
            if key == "Âge":
                if not value.isdigit():
                    await user.send("Merci d'indiquer un âge valide.")
                    return
                age = int(value)
                if age < 15 or age > 35:
                    await user.send("Âge invalide. Réessaie entre 15 et 35.")
                    return
            profil_data[key] = value
        except:
            await user.send("⛔ Temps dépassé ou erreur.")
            return

    profils[user.id] = profil_data
    await poster_profil(interaction, user, profil_data, image_url)

async def poster_profil(interaction, user, data, image_url):
    embed = discord.Embed(
        title=f"{'💖' if data['Genre'].lower() == 'fille' else '💙'} Nouveau profil {'Fille' if data['Genre'].lower() == 'fille' else 'Garçon'} !",
        description="❖ Un nouveau profil vient d'apparaître...\n> Il y a des regards qui racontent plus que mille mots.",
        color=discord.Color.dark_gray()
    )
    embed.add_field(name="Prénom", value=data['Prénom'], inline=False)
    embed.add_field(name="Âge", value=data['Âge'], inline=False)
    embed.add_field(name="Département", value=data['Département'], inline=False)
    embed.add_field(name="Genre", value=data['Genre'], inline=False)
    embed.add_field(name="Orientation", value=data['Orientation'], inline=False)
    embed.add_field(name="Recherche sur le serveur", value=data['Recherche'], inline=False)
    embed.add_field(name="Recherche chez quelqu'un", value=data['Recherche chez quelqu'un'], inline=False)
    embed.add_field(name="Passions", value=data['Passions'], inline=False)
    embed.add_field(name="Description", value=data['Description'], inline=False)
    if image_url:
        embed.set_thumbnail(url=image_url)
    embed.set_footer(text=f"Profil ID: {user.id}")
    embed.set_author(name=f"{user.name}#{user.discriminator}", icon_url=user.avatar.url if user.avatar else None)
    view = ProfilView(user.id)
    target_channel = bot.get_channel(CHANNEL_FILLE if data['Genre'].lower() == 'fille' else CHANNEL_GARCON)
    await target_channel.send(embed=embed, view=view)
    await user.send("✅ Ton profil a bien été publié.")
    log_channel = bot.get_channel(CHANNEL_LOGS)
    await log_channel.send(f"📝 Nouveau profil publié par {user.name}#{user.discriminator} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | ID: {user.id}")

def calcul_compatibilite(age1, age2):
    if not age1 or not age2:
        return None
    pointer_min = (age1 // 2) + 7
    if age2 < pointer_min:
        return 0
    diff = abs(age1 - age2)
    return max(0, 100 - diff * 5)

bot.run(TOKEN)
