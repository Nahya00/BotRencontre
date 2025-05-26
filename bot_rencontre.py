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


def check_pointeur(age1, age2):
    try:
        age1, age2 = int(age1), int(age2)
        min_age = (age1 / 2) + 7
        return age2 < min_age
    except:
        return False


class ContactButton(Button):
    def __init__(self, target_id):
        super().__init__(label="Contacter cette personne", style=discord.ButtonStyle.success)
        self.target_id = target_id

    async def callback(self, interaction: discord.Interaction):
        requester_id = interaction.user.id
        if requester_id not in user_answers or self.target_id not in user_answers:
            await interaction.response.send_message("❌ Impossible de trouver les données du profil.", ephemeral=True)
            return

        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        answers1 = user_answers[requester_id]
        answers2 = user_answers[self.target_id]
        compat = calculate_compatibility(answers1, answers2)

        is_pointeur = check_pointeur(answers1['âge'], answers2['âge'])
        if is_pointeur:
            await interaction.response.send_message("🚨 Écart d'âge inhabituel. Contact bloqué.", ephemeral=True)
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            await log_channel.send(f"🚫 {interaction.user} a tenté de contacter {bot.get_user(self.target_id)} — ÉCART POINTEUR détecté à {now}.")
            return

        if contact_clicks.get(requester_id, 0) >= 3:
            await interaction.response.send_message("❌ Tu as atteint la limite de 3 contacts.", ephemeral=True)
            return

        contact_clicks[requester_id] = contact_clicks.get(requester_id, 0) + 1

        compat_msg = f"Compatibilité : {compat}% "
        if compat >= 90:
            compat_msg += "🟢 Très bonne compatibilité"
        elif compat >= 50:
            compat_msg += "🟡 Bonne compatibilité"
        else:
            compat_msg += "⚠️ Faible compatibilité"

        try:
            user = bot.get_user(self.target_id)
            await user.send(f"📩 {interaction.user} a voulu te contacter !")
        except:
            pass

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(f"📨 {interaction.user} a cliqué sur le bouton de contact du profil de {bot.get_user(self.target_id)} à {now} | {compat_msg}")
        await interaction.response.send_message("✅ La personne a été notifiée si ses MP sont ouverts !", ephemeral=True)


class ReportButton(Button):
    def __init__(self, target_id):
        super().__init__(label="Signaler ce profil", style=discord.ButtonStyle.danger)
        self.target_id = target_id

    async def callback(self, interaction: discord.Interaction):
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(f"🚨 {interaction.user} a signalé le profil de {bot.get_user(self.target_id)} à {now}.")
        await interaction.response.send_message("✅ Le profil a été signalé aux modérateurs.", ephemeral=True)


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
                ("Qu'attends-tu chez quelqu'un ?", "recherche_chez_autrui"),
                ("Tes passions ?", "passions"),
                ("Petite description :", "description"),
            ]

            answers = {}
            await interaction.user.send("**Salut ! On va remplir ta présentation.**")

            for question_text, key in questions:
                valid = False
                while not valid:
                    await interaction.user.send(question_text)
                    msg = await bot.wait_for('message', check=check, timeout=120)

                    if key == "photo":
                        if msg.attachments:
                            answers[key] = msg.attachments[0].url
                            valid = True
                        elif msg.content.lower() == "skip":
                            answers[key] = ""
                            valid = True
                        elif msg.content.startswith("http"):
                            answers[key] = msg.content.strip()
                            valid = True
                        else:
                            await interaction.user.send("❌ Envoie un lien ou une image, ou écris `skip`.")

                    elif key == "âge":
                        if msg.content.isdigit():
                            age = int(msg.content)
                            if 15 <= age <= 35:
                                answers[key] = msg.content
                                valid = True
                            else:
                                await interaction.user.send("❌ Merci d’entrer un âge entre 15 et 35.")
                        else:
                            await interaction.user.send("❌ Réponds uniquement par un chiffre pour l'âge !")
                    elif key == "genre":
                        genre = msg.content.lower()
                        if genre in ["fille", "garçon", "garcon"]:
                            answers[key] = "Garçon" if genre.startswith("gar") else "Fille"
                            valid = True
                        else:
                            await interaction.user.send("❌ Réponds uniquement **Fille** ou **Garçon** !")
                    else:
                        answers[key] = msg.content.strip()
                        valid = True

            user_answers[interaction.user.id] = answers
            genre = answers.get("genre", "").lower()
            color = discord.Color.blue() if "garçon" in genre else discord.Color.magenta()
            title = "💙 Nouveau profil Garçon !" if "garçon" in genre else "💖 Nouveau profil Fille !"
            channel_id = GARCON_CHANNEL_ID if "garçon" in genre else FILLE_CHANNEL_ID
            channel = bot.get_channel(channel_id)

            embed = discord.Embed(
                title=title,
                description="❖ Un nouveau profil vient d'apparaître...\n\n> Il y a des regards qui racontent plus que mille mots.",
                color=color
            )
            embed.set_author(name=interaction.user.name + "#" + interaction.user.discriminator,
                             icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.set_thumbnail(url=answers['photo'] if answers.get('photo') else IMAGE_URL)

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
            view.add_item(ReportButton(interaction.user.id))

            message = await channel.send(embed=embed, view=view)
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            presentation_authors[message.id] = interaction.user.id
            user_profiles[interaction.user.id] = embed

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
            color=discord.Color.dark_theme()
        )
        embed.set_thumbnail(url=IMAGE_URL)
        await channel.send(embed=embed, view=FormButtonView())


bot.run(TOKEN)

