
import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import app_commands
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

LOG_CHANNEL_ID = 1376347435747643475
GIRLS_CHANNEL_ID = 1362035175269077174
BOYS_CHANNEL_ID = 1362035179358781480
WELCOME_CHANNEL_ID = 1362035171301527654

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

user_profiles = {}
presentation_authors = {}
contact_clicks = {}

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Connecté en tant que {bot.user}")
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="Bienvenue sur le système de rencontre",
            description="Remplis ton profil pour apparaître dans les profils mystères et rencontrer d'autres membres.",
            color=discord.Color.from_rgb(15, 15, 15)
        )
        embed.set_author(name="Formulaire Rencontre", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        embed.set_footer(text="Clique sur le bouton ci-dessous pour commencer.")
        view = View()
        view.add_item(Button(label="Remplir mon profil", style=discord.ButtonStyle.primary, custom_id="start_profil"))

        async for msg in channel.history(limit=10):
            if msg.author == bot.user:
                await msg.delete()
        await channel.send(embed=embed, view=view)
def calculate_compatibility(sender, receiver):
    champs = ["recherche", "recherche_chez", "passions"]
    match = sum(1 for champ in champs if sender.get(champ, '').lower() == receiver.get(champ, '').lower())
    return round((match / len(champs)) * 100)

def age_gap_invalid(sender_age, receiver_age):
    return sender_age < ((receiver_age / 2) + 7)

class ContactButton(Button):
    def __init__(self, profile_user_id):
        super().__init__(label="Contacter cette personne", style=discord.ButtonStyle.success)
        self.profile_user_id = profile_user_id

    async def callback(self, interaction: discord.Interaction):
        sender = interaction.user
        receiver_id = self.profile_user_id
        receiver_data = user_profiles.get(receiver_id)
        sender_data = user_profiles.get(sender.id)

        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        if not receiver_data:
            return await interaction.response.send_message("Profil introuvable.", ephemeral=True)

        if sender.id == receiver_id:
            return await interaction.response.send_message("Tu ne peux pas te contacter toi-même.", ephemeral=True)

        contact_clicks.setdefault(sender.id, [])
        if receiver_id in contact_clicks[sender.id]:
            return await interaction.response.send_message("Tu as déjà contacté cette personne.", ephemeral=True)
        if len(contact_clicks[sender.id]) >= 3:
            return await interaction.response.send_message("Tu as atteint la limite de 3 profils contactés.", ephemeral=True)

        contact_clicks[sender.id].append(receiver_id)

        compat_txt = "Compatibilité : inconnue (profil non rempli par le demandeur)"
        if sender_data:
            compat = calculate_compatibility(sender_data, receiver_data)
            if age_gap_invalid(sender_data['âge'], receiver_data['âge']):
                if log_channel:
                    await log_channel.send(f"⚠️ Alerte Pointeur : {sender.name}#{sender.discriminator} ({sender_data['âge']}) → {receiver_data['prénom']} ({receiver_data['âge']}) à {now}")
                return await interaction.response.send_message("Écart d’âge trop important. Respecte autrui.", ephemeral=True)
            if compat >= 90:
                compat_txt = f"Compatibilité : {compat}% ✅ Très bonne compatibilité"
            elif compat <= 30:
                compat_txt = f"Compatibilité : {compat}% ⚠️ Faible compatibilité"
            else:
                compat_txt = f"Compatibilité : {compat}%"

        try:
            await bot.get_user(receiver_id).send(f"📬 {sender.name}#{sender.discriminator} souhaite te contacter !")
        except:
            pass
        try:
            await sender.send(f"Tu as contacté {receiver_data['prénom']} — {compat_txt}")
        except:
            await interaction.response.send_message("Demande envoyée. Impossible de te DM.", ephemeral=True)

        if log_channel:
            await log_channel.send(f"📩 {sender.name}#{sender.discriminator} a cliqué sur [Contacter cette personne] pour {receiver_data['prénom']} à {now} — {compat_txt}")

        await interaction.response.send_message("✅ Demande envoyée !", ephemeral=True)

class ReportButton(Button):
    def __init__(self):
        super().__init__(label="Signaler ce profil", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Profil signalé. Merci.", ephemeral=True)
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            await log_channel.send(f"🚨 {interaction.user.name}#{interaction.user.discriminator} a signalé un profil à {now}.")

class ProfileView(View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.add_item(ContactButton(user_id))
        self.add_item(ReportButton())
class StartProfileButton(Button):
    def __init__(self):
        super().__init__(label="Remplir mon profil", style=discord.ButtonStyle.primary, custom_id="start_profil")

async def create_profile(interaction: discord.Interaction):
    def check(m): return m.author.id == interaction.user.id and m.channel == interaction.channel

    await interaction.response.send_message("Quel est ton prénom ?", ephemeral=True)
    prenom = (await bot.wait_for("message", check=check)).content.strip()

    await interaction.followup.send("Ton âge (15-35) ?", ephemeral=True)
    while True:
        age_msg = await bot.wait_for("message", check=check)
        if age_msg.content.isdigit():
            age = int(age_msg.content)
            if 15 <= age <= 35:
                break
        await interaction.followup.send("Âge invalide. Réessaie entre 15 et 35.", ephemeral=True)

    await interaction.followup.send("Ton département ?", ephemeral=True)
    departement = (await bot.wait_for("message", check=check)).content.strip()

    await interaction.followup.send("Ton genre (Fille / Garçon) ?", ephemeral=True)
    genre = (await bot.wait_for("message", check=check)).content.strip()

    await interaction.followup.send("Ton orientation ?", ephemeral=True)
    orientation = (await bot.wait_for("message", check=check)).content.strip()

    await interaction.followup.send("Que recherches-tu ?", ephemeral=True)
    recherche = (await bot.wait_for("message", check=check)).content.strip()

    await interaction.followup.send("Que recherches-tu chez quelqu'un ?", ephemeral=True)
    recherche_chez = (await bot.wait_for("message", check=check)).content.strip()

    await interaction.followup.send("Tes passions ?", ephemeral=True)
    passions = (await bot.wait_for("message", check=check)).content.strip()

    await interaction.followup.send("Décris-toi :", ephemeral=True)
    description = (await bot.wait_for("message", check=check)).content.strip()

    await interaction.followup.send("Envoie une image ou tape `skip`.", ephemeral=True)
    img_msg = await bot.wait_for("message", check=check)
    image_url = None
    if img_msg.attachments:
        image_url = img_msg.attachments[0].url
    elif img_msg.content.lower().startswith("http"):
        image_url = img_msg.content.strip()

    embed = discord.Embed(
        title=f"{'💖' if genre.lower() == 'fille' else '💙'} Nouveau profil {genre} !",
        description="Un nouveau profil vient d'apparaître...\n\n> Il y a des regards qui racontent plus que mille mots.",
        color=discord.Color.from_rgb(15, 15, 15)
    )
    embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}",
                     icon_url=image_url if image_url else bot.user.avatar.url)
    if image_url:
        embed.set_thumbnail(url=image_url)

    embed.add_field(name="Prénom", value=prenom, inline=False)
    embed.add_field(name="Âge", value=str(age), inline=False)
    embed.add_field(name="Département", value=departement, inline=False)
    embed.add_field(name="Genre", value=genre, inline=False)
    embed.add_field(name="Orientation", value=orientation, inline=False)
    embed.add_field(name="Recherche sur le serveur", value=recherche, inline=False)
    embed.add_field(name="Recherche chez quelqu'un", value=recherche_chez, inline=False)
    embed.add_field(name="Passions", value=passions, inline=False)
    embed.add_field(name="Description", value=description, inline=False)

    user_profiles[interaction.user.id] = {
        "prénom": prenom,
        "âge": age,
        "département": departement,
        "genre": genre,
        "orientation": orientation,
        "recherche": recherche,
        "recherche_chez": recherche_chez,
        "passions": passions,
        "description": description
    }

    view = ProfileView(interaction.user.id)
    channel = bot.get_channel(GIRLS_CHANNEL_ID if genre.lower() == "fille" else BOYS_CHANNEL_ID)
    sent = await channel.send(embed=embed, view=view)
    await sent.add_reaction("✅")
    await sent.add_reaction("❌")
    presentation_authors[sent.id] = interaction.user.id

    await interaction.followup.send("✅ Ton profil a bien été publié !", ephemeral=True)

# Fin de la fonction

bot.run(TOKEN)
