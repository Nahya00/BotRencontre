import discord
from discord.ext import commands
from discord.ui import View, Button
import os
from datetime import datetime
import asyncio

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
DEFAULT_IMAGE_URL = "https://i.imgur.com/FQ4zDtv.gif"

presentation_authors = {}
user_profiles = {}
contact_clicks = {}
user_answers = {}

class ContactButton(Button):
    def __init__(self, author_id):
        super().__init__(label="Contacter cette personne", style=discord.ButtonStyle.success)
        self.author_id = author_id

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id == self.author_id:
            await interaction.response.send_message("❌ Tu ne peux pas contacter ton propre profil.", ephemeral=True)
            return
        if user_id not in contact_clicks:
            contact_clicks[user_id] = []
        if self.author_id in contact_clicks[user_id]:
            await interaction.response.send_message("❌ Tu as déjà contacté ce profil.", ephemeral=True)
            return
        if len(contact_clicks[user_id]) >= 3:
            await interaction.response.send_message("❌ Tu as atteint la limite de 3 tentatives de contact.", ephemeral=True)
            return

        contact_clicks[user_id].append(self.author_id)

        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        sender_tag = f"{interaction.user.name}#{interaction.user.discriminator}"
        receiver_user = await bot.fetch_user(self.author_id)
        receiver_tag = f"{receiver_user.name}#{receiver_user.discriminator}"

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(f"📬 `{sender_tag}` a cliqué sur le bouton de contact du profil de `{receiver_tag}` à {now}")

        try:
            await receiver_user.send(f"📩 {sender_tag} a voulu te contacter via ton profil.")
        except:
            pass

        if self.author_id in user_answers and user_id in user_answers:
            compatibility = calculate_compatibility(user_answers[self.author_id], user_answers[user_id])
            embed = discord.Embed(title="📊 Compatibilité détectée",
                                  description=f"Tu es compatible à **{compatibility}%** avec cette personne.",
                                  color=discord.Color.blurple())
            await interaction.user.send(embed=embed)

        await interaction.response.send_message("✅ Demande envoyée (si la personne a ses MP ouverts).", ephemeral=True)

class SignalButton(Button):
    def __init__(self):
        super().__init__(label="Signaler ce profil", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        log = bot.get_channel(LOG_CHANNEL_ID)
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        await log.send(f"⚠️ `{interaction.user.name}#{interaction.user.discriminator}` a **signalé** un profil à {now}.")
        await interaction.response.send_message("Le profil a été signalé. Merci pour ta vigilance.", ephemeral=True)

class FormButton(Button):
    def __init__(self):
        super().__init__(label="Remplir ma présentation", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Je t'ai envoyé un DM pour commencer ta présentation !", ephemeral=True)

        def check(m):
            return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

        try:
            questions = [
                ("Quel est ton **prénom** ?", "prénom"),
                ("Quel est ton **âge** ? (entre 15 et 35)", "âge"),
                ("Dans quel **département** es-tu ?", "département"),
                ("Quel est ton **genre** (Fille / Garçon) ?", "genre"),
                ("Quelle est ton **orientation** (Hétéro / Homo / Bi / Pan / Autre) ?", "orientation"),
                ("Que recherches-tu sur ce serveur ?", "recherche"),
                ("Qu'attends-tu chez quelqu'un ?", "recherche_chez_autrui"),
                ("Tes passions ?", "passions"),
                ("Petite description :", "description"),
                ("Si tu veux, envoie un **lien d'image** à afficher sur ton profil (ou écris `skip`).", "photo")
            ]

            answers = {}
            await interaction.user.send("**Salut ! On va remplir ta présentation 💬**")

            for question_text, key in questions:
                valid = False
                while not valid:
                    await interaction.user.send(question_text + "​")
                    msg = await bot.wait_for('message', check=check, timeout=120)
                    content = msg.content.strip()

                    if key == "âge":
                        if content.isdigit():
                            age = int(content)
                            if 15 <= age <= 35:
                                answers[key] = content
                                valid = True
                            else:
                                await interaction.user.send("❌ Merci d’entrer un âge entre 15 et 35.")
                        else:
                            await interaction.user.send("❌ Merci de répondre uniquement par un chiffre.")
                    elif key == "genre":
                        if content.lower() in ["fille", "garçon", "garcon"]:
                            answers[key] = "Fille" if content.lower() == "fille" else "Garçon"
                            valid = True
                        else:
                            await interaction.user.send("❌ Merci de répondre Fille ou Garçon uniquement.")
                    elif key == "photo":
                        if content.lower().startswith("http"):
                            answers[key] = content
                        else:
                            answers[key] = DEFAULT_IMAGE_URL
                        valid = True
                    else:
                        answers[key] = content
                        valid = True
                    await asyncio.sleep(1.2)

            user_answers[interaction.user.id] = answers
            genre = answers["genre"].lower()

            if genre == "fille":
                title = "🖤 Nouveau profil Fille !"
                channel = bot.get_channel(FILLE_CHANNEL_ID)
                color = discord.Color.from_str("#000000")
            else:
                title = "🖤 Nouveau profil Garçon !"
                channel = bot.get_channel(GARCON_CHANNEL_ID)
                color = discord.Color.from_str("#000000")

            embed = discord.Embed(
                title=title,
                description="❖ Un nouveau profil vient d'apparaître.../n> Il y a des regards qui racontent plus que mille mots.",
                color=color
            )
            embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}",
                             icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.set_thumbnail(url=answers["photo"] or DEFAULT_IMAGE_URL)
            embed.add_field(name="Prénom", value=answers['prénom'], inline=True)
            embed.add_field(name="Âge", value=answers['âge'], inline=True)
            embed.add_field(name="Département", value=answers['département'], inline=True)
            embed.add_field(name="Genre", value=answers['genre'], inline=True)
            embed.add_field(name="Orientation", value=answers['orientation'], inline=True)
            embed.add_field(name="Recherche sur le serveur", value=answers['recherche'], inline=False)
            embed.add_field(name="Recherche chez quelqu'un", value=answers['recherche_chez_autrui'], inline=False)
            embed.add_field(name="Passions", value=answers['passions'], inline=False)
            embed.add_field(name="Description", value=answers['description'], inline=False)

            view = View()
            view.add_item(ContactButton(interaction.user.id))
            view.add_item(SignalButton())

            message = await channel.send(embed=embed, view=view)
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            presentation_authors[message.id] = interaction.user.id
            user_profiles[interaction.user.id] = embed

            await interaction.user.send("✅ Ton profil a bien été envoyé !")
        except Exception as e:
            await interaction.user.send(f"❌ Une erreur est survenue pendant ta présentation : {e}")

class FormButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FormButton())

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    channel = bot.get_channel(ACCUEIL_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🖤 Bienvenue dans l'antre des âmes liées...",
            description="> Viens glisser ton histoire parmi les regards silencieux./n> Clique sur le bouton ci-dessous pour déposer ton profil, et laisse le destin s'en mêler.",
            color=discord.Color.from_str("#000000")
        )
        embed.set_thumbnail(url=DEFAULT_IMAGE_URL)
        await channel.send(embed=embed, view=FormButtonView())

def calculate_compatibility(answers1, answers2):
    keys = ['genre', 'orientation', 'recherche', 'recherche_chez_autrui', 'passions']
    matches = sum(1 for key in keys if key in answers1 and key in answers2 and answers1[key].lower() == answers2[key].lower())
    return int((matches / len(keys)) * 100)

bot.run(TOKEN)
