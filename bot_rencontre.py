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

def calculate_compatibility(answers1, answers2):
    keys = ['genre', 'orientation', 'recherche', 'recherche_chez_autrui', 'passions']
    matches = sum(1 for key in keys if key in answers1 and key in answers2 and answers1[key].lower() == answers2[key].lower())
    return int((matches / len(keys)) * 100)

class FormButton(Button):
    def __init__(self):
        super().__init__(label="Remplir ma présentation", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Je t'ai envoyé un DM pour commencer ta présentation !", ephemeral=True)

        def check(m):
            return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

        try:
            questions = [
                ("Si tu veux, tu peux envoyer une **photo** à afficher dans ton profil. Sinon, écris `skip`.", "photo"),
                ("Quel est ton **prénom** ?", "prénom"),
                ("Quel est ton **âge** ? (entre 15 et 35)", "âge"),
                ("Dans quel **département** es-tu ?", "département"),
                ("Quel est ton **genre** (Fille / Garçon) ?", "genre"),
                ("Quelle est ton **orientation** (Hétéro / Homo / Bi / Pan / Autre) ?", "orientation"),
                ("Que recherches-tu sur ce serveur ?", "recherche"),
                ("Qu'est-ce que tu recherches chez quelqu'un ?", "recherche_chez_autrui"),
                ("Quels sont tes **passions / centres d'intérêt** ?", "passions"),
                ("Fais une **petite description** de toi :", "description"),
            ]

            answers = {}
            await interaction.user.send("**Salut ! On va remplir ta présentation 💬**")

            for question_text, key in questions:
                valid = False
                while not valid:
                    await interaction.user.send(question_text)
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
                            await interaction.user.send("❌ Merci de répondre uniquement par un chiffre pour l'âge !")
                    elif key == "genre":
                        genre = content.lower()
                        if genre in ["fille", "garçon", "garcon"]:
                            answers[key] = "Garçon" if genre.startswith("gar") else "Fille"
                            valid = True
                        else:
                            await interaction.user.send("❌ Merci de répondre uniquement **Fille** ou **Garçon** !")
                    elif key == "photo" and msg.attachments:
                        answers[key] = msg.attachments[0].url
                        valid = True
                    elif key == "photo" and content.lower() == "skip":
                        valid = True
                    elif key == "photo" and content.startswith("http"):
                        answers[key] = content
                        valid = True
                    elif key == "photo":
                        await interaction.user.send("❌ Envoie un lien ou une image, ou écris `skip`.")
                    else:
                        answers[key] = content
                        valid = True

            user_answers[interaction.user.id] = answers
            genre = answers.get("genre", "").lower()

            if "fille" in genre:
                color = discord.Color.dark_magenta()
                title = "💖 Nouveau profil Fille !"
                channel = bot.get_channel(FILLE_CHANNEL_ID)
            else:
                color = discord.Color.dark_blue()
                title = "💙 Nouveau profil Garçon !"
                channel = bot.get_channel(GARCON_CHANNEL_ID)

            embed = discord.Embed(
                title=title,
                description="❖ Un nouveau profil vient d'apparaître...\n\n> Il y a des regards qui racontent plus que mille mots.",
                color=color
            )
            embed.set_author(name=interaction.user.name + "#" + interaction.user.discriminator, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.add_field(name="Prénom", value=answers['prénom'], inline=True)
            embed.add_field(name="Âge", value=answers['âge'], inline=True)
            embed.add_field(name="Département", value=answers['département'], inline=True)
            embed.add_field(name="Genre", value=answers['genre'], inline=True)
            embed.add_field(name="Orientation", value=answers['orientation'], inline=True)
            embed.add_field(name="Recherche sur le serveur", value=answers['recherche'], inline=False)
            embed.add_field(name="Recherche chez quelqu'un", value=answers['recherche_chez_autrui'], inline=False)
            embed.add_field(name="Passions", value=answers['passions'], inline=False)
            embed.add_field(name="Description", value=answers['description'], inline=False)
            thumbnail_url = answers['photo'] if 'photo' in answers and answers['photo'].startswith('http') else IMAGE_URL
            embed.set_thumbnail(url=thumbnail_url)

            message = await channel.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            presentation_authors[message.id] = interaction.user.id
            user_profiles[interaction.user.id] = embed

            await interaction.user.send("Ta présentation a été envoyée avec succès ! 💖")

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
            description="> Viens glisser ton histoire parmi les regards silencieux.\n> Clique sur le bouton ci-dessous pour déposer ton profil, et laisse le destin s'en mêler.",
            color=discord.Color.from_str("#000000")
        )
        embed.set_thumbnail(url=IMAGE_URL)
        await channel.send(embed=embed, view=FormButtonView())

bot.run(TOKEN)
