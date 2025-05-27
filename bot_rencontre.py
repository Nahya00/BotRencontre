import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

CHANNEL_FILLE = 1362035175269077174
CHANNEL_GARCON = 1362035179358781480
CHANNEL_LOGS = 1376347435747643475
CHANNEL_ACCUEIL = 1362035171301527654

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

profils = {}
contact_clicks = {}

class StartProfilButton(Button):
    def __init__(self):
        super().__init__(label="Remplir mon profil", style=discord.ButtonStyle.primary, custom_id="start_profil")

    async def callback(self, interaction: discord.Interaction):
        await create_profile(interaction)

class StartProfilView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StartProfilButton())

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    accueil_channel = bot.get_channel(CHANNEL_ACCUEIL)
    if accueil_channel:
        embed = discord.Embed(
            title="Rencontre Mystère Noctys",
            description="**Clique ci-dessous pour créer ton profil anonyme.**\nLes regards ne mentent jamais...",
            color=discord.Color.from_rgb(20, 20, 20)
        )
        embed.set_footer(text="Noctys • Ambiance mystique")
        embed.set_author(name="Système de Rencontre", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await accueil_channel.purge(limit=5)
        await accueil_channel.send(embed=embed, view=StartProfilView())
async def create_profile(interaction: discord.Interaction):
    def check(m): return m.author.id == interaction.user.id and m.channel == interaction.channel

    await interaction.response.send_message("Envoie une **image** (ou `skip` pour passer)", ephemeral=True)
    try:
        msg = await bot.wait_for("message", check=check, timeout=120)
        if msg.attachments:
            image_url = msg.attachments[0].url
        elif msg.content.lower().startswith("http"):
            image_url = msg.content.strip()
        elif msg.content.lower() == "skip":
            image_url = None
        else:
            await interaction.followup.send("❌ Envoie une image, un lien ou tape `skip`.", ephemeral=True)
            return
    except:
        await interaction.followup.send("⛔ Temps dépassé ou erreur.", ephemeral=True)
        return

    questions = [
        ("Quel est ton prénom ?", "Prénom"),
        ("Ton âge (15-35) ?", "Âge"),
        ("Département ?", "Département"),
        ("Genre (Fille / Garçon) ?", "Genre"),
        ("Orientation ?", "Orientation"),
        ("Que recherches-tu sur ce serveur ?", "Recherche"),
        ("Qu'attends-tu chez quelqu'un ?", "Recherche_chez"),
        ("Tes passions ?", "Passions"),
        ("Petite description :", "Description")
    ]

    data = {}

    for q, key in questions:
        await interaction.followup.send(q, ephemeral=True)
        try:
            r = await bot.wait_for("message", check=check, timeout=120)
            val = r.content.strip()
            if key == "Âge":
                if not val.isdigit():
                    await interaction.followup.send("❌ Merci d’indiquer un âge valide.", ephemeral=True)
                    return
                age = int(val)
                if age < 15 or age > 35:
                    await interaction.followup.send("❌ Âge non autorisé (15-35).", ephemeral=True)
                    return
                data[key] = age
            else:
                data[key] = val
        except:
            await interaction.followup.send("⛔ Temps dépassé ou erreur.", ephemeral=True)
            return

    profils[interaction.user.id] = data
    await poster_profil(interaction, data, image_url)
class ProfilView(View):
    def __init__(self, auteur_id):
        super().__init__(timeout=None)
        self.auteur_id = auteur_id
        self.add_item(ContactButton(auteur_id))
        self.add_item(ReportButton())

class ContactButton(Button):
    def __init__(self, cible_id):
        super().__init__(label="Contacter cette personne", style=discord.ButtonStyle.success, custom_id="contact")
        self.cible_id = cible_id

    async def callback(self, interaction: discord.Interaction):
        sender_id = interaction.user.id
        receiver_id = self.cible_id

        if sender_id == receiver_id:
            return await interaction.response.send_message("Tu ne peux pas te contacter toi-même.", ephemeral=True)

        sender = profils.get(sender_id)
        receiver = profils.get(receiver_id)

        log = f"📩 {interaction.user.name}#{interaction.user.discriminator} a cliqué sur [Contacter cette personne] pour {receiver['Prénom']} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        compat_txt = "Compatibilité inconnue"

        if sender and receiver:
            compat = calcul_compatibilite(sender["Âge"], receiver["Âge"])
            if compat == 0:
                await interaction.response.send_message("Cet écart d'âge est inapproprié. Respecte autrui.", ephemeral=True)
                await bot.get_channel(CHANNEL_LOGS).send(f"⚠️ Alerte Pointeur : {interaction.user.name}#{interaction.user.discriminator} ({sender['Âge']}) → {receiver['Prénom']} ({receiver['Âge']})")
                return
            compat_txt = f"Compatibilité : {compat}% ✅" if compat >= 90 else f"Compatibilité : {compat}%"
            try:
                await interaction.user.send(f"Tu as contacté {receiver['Prénom']} — {compat_txt}")
            except:
                pass

            try:
                await bot.get_user(receiver_id).send(f"{interaction.user.name}#{interaction.user.discriminator} a voulu te contacter.")
            except:
                pass

        await bot.get_channel(CHANNEL_LOGS).send(f"{log} — {compat_txt}")
        await interaction.response.send_message("✅ Demande envoyée.", ephemeral=True)

class ReportButton(Button):
    def __init__(self):
        super().__init__(label="Signaler ce profil", style=discord.ButtonStyle.danger, custom_id="report")

    async def callback(self, interaction: discord.Interaction):
        await bot.get_channel(CHANNEL_LOGS).send(f"🚨 {interaction.user.name}#{interaction.user.discriminator} a signalé un profil à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        await interaction.response.send_message("Le profil a été signalé. Merci.", ephemeral=True)

def calcul_compatibilite(age1, age2):
    pointer = (age1 / 2) + 7
    if age2 < pointer:
        return 0
    diff = abs(age1 - age2)
    return max(0, 100 - diff * 4)

async def poster_profil(interaction, data, image_url):
    embed = discord.Embed(
        title=f"{'💖' if data['Genre'].lower() == 'fille' else '💙'} Nouveau profil {data['Genre']} !",
        description="Un nouveau profil vient d'apparaître...\n\n> Les mystères de la nuit n’ont pas fini de nous surprendre.",
        color=discord.Color.from_rgb(20, 20, 20)
    )
    embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    if image_url:
        embed.set_thumbnail(url=image_url)

    embed.add_field(name="Prénom", value=data["Prénom"], inline=False)
    embed.add_field(name="Âge", value=str(data["Âge"]), inline=False)
    embed.add_field(name="Département", value=data["Département"], inline=False)
    embed.add_field(name="Genre", value=data["Genre"], inline=False)
    embed.add_field(name="Orientation", value=data["Orientation"], inline=False)
    embed.add_field(name="Recherche", value=data["Recherche"], inline=False)
    embed.add_field(name="Recherche chez quelqu'un", value=data["Recherche_chez"], inline=False)
    embed.add_field(name="Passions", value=data["Passions"], inline=False)
    embed.add_field(name="Description", value=data["Description"], inline=False)
    embed.set_footer(text=f"Profil ID: {interaction.user.id}")

    target_channel = bot.get_channel(CHANNEL_FILLE if data["Genre"].lower() == "fille" else CHANNEL_GARCON)
    msg = await target_channel.send(embed=embed, view=ProfilView(interaction.user.id))
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    await interaction.followup.send("✅ Ton profil a bien été publié !", ephemeral=True)
    await bot.get_channel(CHANNEL_LOGS).send(f"📝 Nouveau profil par {interaction.user.name}#{interaction.user.discriminator} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} — ID {interaction.user.id}")


bot.run(TOKEN)
