import discord
from discord.ext import commands
from discord.ui import View, Button
import os
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("TOKEN")

ACCUEIL_CHANNEL_ID = 1362035171301527654
FILLE_CHANNEL_ID = 1362035175269077174
GARCON_CHANNEL_ID = 1362035179358781480
LOG_CHANNEL_ID = 1376347435747643475
IMAGE_URL = "https://i.imgur.com/FQ4zDtv.gif"

presentation_authors = {}
user_profiles = {}
contact_clicks = {}
user_answers = {}

def calculate_compatibility(a1, a2):
    keys = ['genre', 'orientation', 'recherche', 'recherche_chez_autrui', 'passions']
    matches = sum(1 for key in keys if key in a1 and key in a2 and a1[key].lower() == a2[key].lower())
    return int((matches / len(keys)) * 100)

def age_pointer_limit(age):
    return int(age / 2 + 7)

class ContactButton(Button):
    def __init__(self, target_user_id):
        super().__init__(label="Contacter cette personne", style=discord.ButtonStyle.success)
        self.target_user_id = target_user_id

    async def callback(self, interaction: discord.Interaction):
        if self.target_user_id == interaction.user.id:
            await interaction.response.send_message("❌ Tu ne peux pas te contacter toi-même.", ephemeral=True)
            return

        clicks = contact_clicks.get(interaction.user.id, 0)
        if clicks >= 3:
            await interaction.response.send_message("❌ Tu as atteint la limite de 3 demandes de contact.", ephemeral=True)
            return

        contact_clicks[interaction.user.id] = clicks + 1
        sender_answers = user_answers.get(interaction.user.id)
        target_answers = user_answers.get(self.target_user_id)

        if not sender_answers or not target_answers:
            await interaction.response.send_message("❌ Impossible de vérifier la compatibilité.", ephemeral=True)
            return

        sender_age = int(sender_answers.get("âge", 0))
        target_age = int(target_answers.get("âge", 0))
        min_target_age = age_pointer_limit(sender_age)

        if target_age < min_target_age:
            await interaction.response.send_message("⚠️ Cet écart d’âge est inhabituel. Merci de respecter autrui.", ephemeral=True)
            log = bot.get_channel(LOG_CHANNEL_ID)
            await log.send(f"⚠️ {interaction.user.name}#{interaction.user.discriminator} ({sender_age}) a tenté de contacter {bot.get_user(self.target_user_id)} ({target_age}) → Écart d’âge inapproprié.")
            return

        compatibility = calculate_compatibility(sender_answers, target_answers)
        log = bot.get_channel(LOG_CHANNEL_ID)
        await log.send(f"✉️ {interaction.user.name}#{interaction.user.discriminator} a cliqué sur le bouton de contact du profil de {bot.get_user(self.target_user_id)} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Compatibilité : {compatibility}% {'⚠️ (Faible compatibilité)' if compatibility < 40 else ''}")

        try:
            await bot.get_user(self.target_user_id).send(f"✉️ {interaction.user.name}#{interaction.user.discriminator} a voulu te contacter suite à ton profil posté sur le serveur.")
            await interaction.response.send_message("✅ Demande envoyée avec succès !", ephemeral=True)
        except:
            await interaction.response.send_message("⚠️ Cette personne a les messages privés fermés.", ephemeral=True)

class SignalButton(Button):
    def __init__(self, target_user_id):
        super().__init__(label="Signaler ce profil", style=discord.ButtonStyle.danger)
        self.target_user_id = target_user_id

    async def callback(self, interaction: discord.Interaction):
        log = bot.get_channel(LOG_CHANNEL_ID)
        await log.send(f"🚨 {interaction.user.name}#{interaction.user.discriminator} a signalé le profil de {bot.get_user(self.target_user_id)} à {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        await interaction.response.send_message("Merci pour ta vigilance. L’équipe de modération a été notifiée.", ephemeral=True)

class FormButton(Button):
    def __init__(self):
        super().__init__(label="Remplir ma présentation", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Je t’ai envoyé un DM pour commencer ta présentation !", ephemeral=True)

        def check(m):
            return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

        try:
            questions = [
                ("Envoie une image ou un lien, ou écris `skip`.", "photo"),
                ("Quel est ton prénom ?", "prénom"),
                ("Quel est ton âge ? (entre 15 et 35)", "âge"),
                ("Dans quel département es-tu ?", "département"),
                ("Quel est ton genre (Fille / Garçon) ?", "genre"),
                ("Orientation (Hétéro / Homo / Bi / Pan / Autre)", "orientation"),
                ("Que recherches-tu sur ce serveur ?", "recherche"),
                ("Qu’attends-tu chez quelqu’un ?", "recherche_chez_autrui"),
                ("Tes passions ?", "passions"),
                ("Petite description :", "description"),
            ]

            answers = {}
            await interaction.user.send("**Salut ! On va remplir ta présentation.**")

            for question, key in questions:
                valid = False
                while not valid:
                    await interaction.user.send(question)
                    msg = await bot.wait_for('message', check=check, timeout=120)
                    content = msg.content.strip()

                    if key == "âge":
                        if content.isdigit() and 15 <= int(content) <= 35:
                            answers[key] = content
                            valid = True
                        else:
                            await interaction.user.send("❌ Âge invalide. Entre un nombre entre 15 et 35.")
                    elif key == "genre":
                        genre = content.lower()
                        if genre in ["fille", "garçon", "garcon"]:
                            answers[key] = "Garçon" if genre.startswith("gar") else "Fille"
                            valid = True
                        else:
                            await interaction.user.send("❌ Réponds uniquement par Fille ou Garçon.")
                    elif key == "photo":
                        if msg.attachments and msg.attachments[0].url.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                            answers[key] = msg.attachments[0].url
                            valid = True
                        elif content.lower() == "skip" or content.startswith("http"):
                            answers[key] = content if content.lower() != "skip" else None
                            valid = True
                        else:
                            await interaction.user.send("❌ Envoie un lien ou une image, ou écris `skip`.")
                    else:
                        answers[key] = content
                        valid = True

            user_answers[interaction.user.id] = answers
            genre = answers['genre'].lower()
            channel_id = FILLE_CHANNEL_ID if genre == "fille" else GARCON_CHANNEL_ID
            color = discord.Color.dark_embed()
            title = f"🖤 Nouveau profil {'Fille' if genre == 'fille' else 'Garçon'} !"
            channel = bot.get_channel(channel_id)

            embed = discord.Embed(title=title, description="❖ Un nouveau profil vient d'apparaître...\n\n> Il y a des regards qui racontent plus que mille mots.", color=color)
            embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.set_thumbnail(url=answers['photo'] if answers['photo'] else IMAGE_URL)
            embed.add_field(name="Prénom", value=answers['prénom'], inline=True)
            embed.add_field(name="Âge", value=answers['âge'], inline=True)
            embed.add_field(name="Département", value=answers['département'], inline=True)
            embed.add_field(name="Genre", value=answers['genre'], inline=True)
            embed.add_field(name="Orientation", value=answers['orientation'], inline=True)
            embed.add_field(name="Recherche sur le serveur", value=answers['recherche'], inline=False)
            embed.add_field(name="Recherche chez quelqu'un", value=answers['recherche_chez_autrui'], inline=False)
            embed.add_field(name="Passions", value=answers['passions'], inline=False)
            embed.add_field(name="Description", value=answers['description'], inline=False)

            view = View(timeout=None)
            view.add_item(ContactButton(interaction.user.id))
            view.add_item(SignalButton(interaction.user.id))

            msg = await channel.send(embed=embed, view=view)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

            presentation_authors[msg.id] = interaction.user.id
            user_profiles[interaction.user.id] = embed

            await interaction.user.send("✅ Ton profil a bien été envoyé !")

        except Exception as e:
            await interaction.user.send(f"❌ Erreur pendant la présentation : {e}")

class FormButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FormButton())

@bot.event
async def on_ready():
    print(f"Bot prêt : {bot.user}")
    channel = bot.get_channel(ACCUEIL_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="💘 Fais des rencontres ici !",
            description="Bienvenue sur notre espace rencontre !\nClique sur le bouton ci-dessous pour remplir ta fiche et te présenter aux autres.\n\nQue l'amour ou l'amitié commence !",
            color=discord.Color.from_str("#000000")
        )
        embed.set_thumbnail(url=IMAGE_URL)
        await channel.send(embed=embed, view=FormButtonView())

bot.run(TOKEN)
