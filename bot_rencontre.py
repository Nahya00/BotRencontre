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
            ("Genre ? (Garçon / Fille / Autre)", "Genre"),
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
        embed.set_footer(text="Noctys • Ambiance mystique")
        embed.set_author(name="Système de Rencontre", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await accueil_channel.send(embed=embed, view=StartProfilView())
        class ProfilView(View):
    def __init__(self, auteur_id):
        super().__init__(timeout=None)
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

        compat_txt = "Compatibilité inconnue"
        log = f"📩 {interaction.user} a cliqué sur Contacter {receiver['Prénom']} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"

        if sender and receiver:
            compat = calcul_compatibilite(int(sender["Âge"]), int(receiver["Âge"]))
            if compat == 0:
                await interaction.response.send_message("Cet écart d'âge est inapproprié. Respecte autrui.", ephemeral=True)
                await bot.get_channel(CHANNEL_LOGS).send(f"⚠️ Alerte pointeur : {interaction.user} → {receiver['Prénom']} ({receiver['Âge']})")
                return
            compat_txt = f"Compatibilité : {compat}% ✅" if compat >= 90 else f"Compatibilité : {compat}%"
            try:
                await interaction.user.send(f"Tu as contacté {receiver['Prénom']} — {compat_txt}")
            except:
                pass
            try:
                await bot.get_user(receiver_id).send(f"{interaction.user} a voulu te contacter.")
            except:
                pass

        await bot.get_channel(CHANNEL_LOGS).send(f"{log} — {compat_txt}")
        await interaction.response.send_message("✅ Demande envoyée.", ephemeral=True)

class ReportButton(Button):
    def __init__(self):
        super().__init__(label="Signaler ce profil", style=discord.ButtonStyle.danger, custom_id="report")

    async def callback(self, interaction: discord.Interaction):
        await bot.get_channel(CHANNEL_LOGS).send(f"🚨 {interaction.user} a signalé un profil à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
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
    embed.set_author(name=f"{interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    if image_url:
        embed.set_thumbnail(url=image_url)

    for champ, titre in [
        ("Prénom", "Prénom"),
        ("Âge", "Âge"),
        ("Département", "Département"),
        ("Genre", "Genre"),
        ("Orientation", "Orientation"),
        ("Recherche", "Recherche"),
        ("Recherche chez quelqu'un", "Recherche chez quelqu'un"),
        ("Passions", "Passions"),
        ("Description", "Description")
    ]:
        embed.add_field(name=titre, value=str(data[champ]), inline=False)

    embed.set_footer(text=f"Profil ID: {interaction.user.id}")
    target_channel = bot.get_channel(CHANNEL_FILLE if data["Genre"].lower() == "fille" else CHANNEL_GARCON)
    msg = await target_channel.send(embed=embed, view=ProfilView(interaction.user.id))
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    await bot.get_channel(CHANNEL_LOGS).send(
        f"📝 Profil publié par {interaction.user} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | ID: {interaction.user.id}"
    )

bot.run(TOKEN)
