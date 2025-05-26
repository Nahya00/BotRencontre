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

        if len(contact_clicks[user_id]) >= 3:
            await interaction.response.send_message("❌ Tu as déjà utilisé tes 3 tentatives de contact.", ephemeral=True)
            return

        contact_clicks[user_id].append(self.author_id)

        try:
            compatibility = calculate_compatibility(user_answers[user_id], user_answers[self.author_id])
        except:
            compatibility = "?"

        try:
            receiver = await bot.fetch_user(self.author_id)
            await receiver.send(f"📩 {interaction.user.name}#{interaction.user.discriminator} a cliqué sur ton profil !")
        except:
            pass

        await interaction.user.send(f"📊 Tu es compatible à environ {compatibility}% avec cette personne.")

        log = bot.get_channel(LOG_CHANNEL_ID)
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        sender = f"{interaction.user.name}#{interaction.user.discriminator}"
        receiver_tag = f"{receiver.name}#{receiver.discriminator}" if 'receiver' in locals() else "?"
        await log.send(f"📬 `{sender}` a cliqué sur le profil de `{receiver_tag}` à {now}")

        await interaction.response.send_message("✅ Action enregistrée.", ephemeral=True)

class SignalButton(Button):
    def __init__(self):
        super().__init__(label="Signaler ce profil", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        log = bot.get_channel(LOG_CHANNEL_ID)
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        await log.send(f"⚠️ `{interaction.user.name}#{interaction.user.discriminator}` a signalé un profil à {now}")
        await interaction.response.send_message("Merci, ton signalement a été enregistré.", ephemeral=True)

class FormButton(Button):
    def __init__(self):
        super().__init__(label="Remplir ma présentation", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Je t’ai envoyé un DM !", ephemeral=True)

        def check(m): return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

        try:
            questions = [
                ("Quel est ton prénom ?", "prénom"),
                ("Quel est ton âge ? (15-35)", "âge"),
                ("Département ?", "département"),
                ("Genre (Fille / Garçon) ?", "genre"),
                ("Orientation (Hétéro / Homo / Bi / Pan / Autre) ?", "orientation"),
                ("Que recherches-tu sur ce serveur ?", "recherche"),
                ("Qu'attends-tu chez quelqu'un ?", "recherche_chez_autrui"),
                ("Tes passions ?", "passions"),
                ("Petite description :", "description")
            ]

            answers = {}
            await interaction.user.send("On va remplir ton profil !")

            for q, key in questions:
                valid = False
                while not valid:
                    await interaction.user.send(q)
                    msg = await bot.wait_for('message', check=check, timeout=120)
                    content = msg.content.strip()

                    if key == "âge":
                        if content.isdigit():
                            age = int(content)
                            if 15 <= age <= 35:
                                answers[key] = content
                                valid = True
                            else:
                                await interaction.user.send("Entre un âge entre 15 et 35.")
                        else:
                            await interaction.user.send("Entre un âge valide (chiffre uniquement).")
                    elif key == "genre":
                        if content.lower() in ["fille", "garçon", "garcon"]:
                            answers[key] = "Fille" if "fille" in content.lower() else "Garçon"
                            valid = True
                        else:
                            await interaction.user.send("Répond uniquement par Fille ou Garçon.")
                    else:
                        answers[key] = content
                        valid = True

            user_answers[interaction.user.id] = answers

            genre = answers['genre'].lower()
            channel = bot.get_channel(FILLE_CHANNEL_ID if "fille" in genre else GARCON_CHANNEL_ID)
            title = "🖤 Nouveau profil Fille !" if "fille" in genre else "🖤 Nouveau profil Garçon !"
            color = discord.Color.from_str("#000000")

            embed = discord.Embed(
                title=title,
              description="❖ Un nouveau profil vient d'apparaître...\n> Il y a des regards qui racontent plus que mille mots."
            )
            embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}",
                             icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.set_thumbnail(url=IMAGE_URL)
            for field, val in answers.items():
                embed.add_field(name=field.capitalize(), value=val, inline=False)

            view = View()
            view.add_item(ContactButton(interaction.user.id))
            view.add_item(SignalButton())

            message = await channel.send(embed=embed, view=view)
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            await interaction.user.send("✅ Ton profil a bien été envoyé !")

        except Exception as e:
            await interaction.user.send(f"❌ Une erreur est survenue : {e}")

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
