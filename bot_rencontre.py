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
IMAGE_URL = "https://i.imgur.com/FQ4zDtv.gif"

presentation_authors = {}
user_profiles = {}
contact_clicks = {}
user_answers = {}

def calculate_compatibility(a1, a2):
    keys = ["genre", "orientation", "recherche", "recherche_chez_autrui", "passions"]
    matches = sum(1 for key in keys if a1.get(key, "").lower() == a2.get(key, "").lower())
    return int((matches / len(keys)) * 100)
class FormButton(Button):
    def __init__(self):
        super().__init__(label="Remplir ma présentation", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("📩 Je t'ai envoyé un DM pour commencer ta présentation.", ephemeral=True)

        def check(m):
            return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

        try:
            questions = [
                ("Si tu veux, tu peux envoyer une **photo** en pièce jointe ou lien. Sinon, écris `skip`.", "photo"),
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
            await interaction.user.send("**On commence ! Réponds à chaque question :**")

            for question_text, key in questions:
                valid = False
                while not valid:
                    await interaction.user.send(question_text + "\u200B")
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
                            await interaction.user.send("❌ Merci de répondre par Fille ou Garçon uniquement.")
                    elif key == "photo":
                        if msg.attachments and msg.attachments[0].url.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                            answers[key] = msg.attachments[0].url
                            valid = True
                        elif content.lower().startswith("http"):
                            answers[key] = content
                            valid = True
                        elif content.lower() == "skip":
                            answers[key] = None
                            valid = True
                        else:
                            await interaction.user.send("❌ Envoie un lien ou une image, ou écris `skip`.")
                    else:
                        answers[key] = content
                        valid = True

                    await asyncio.sleep(1.2)

            user_answers[interaction.user.id] = answers
            genre = answers.get("genre", "").lower()
            age = int(answers.get("âge", 0))
            thumbnail = answers.get("photo") or IMAGE_URL

            # Détection de salon et couleur
            if genre == "fille":
                title = "💖 Nouveau profil Fille !"
                channel = bot.get_channel(FILLE_CHANNEL_ID)
                color = discord.Color.from_str("#FFC0CB")
            else:
                title = "💙 Nouveau profil Garçon !"
                channel = bot.get_channel(GARCON_CHANNEL_ID)
                color = discord.Color.from_str("#87CEFA")

            embed = discord.Embed(
                title=title,
                description="❖ Un nouveau profil vient d'apparaître...\n\n> Il y a des regards qui racontent plus que mille mots.",
                color=color
            )
            embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}",
                             icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.set_thumbnail(url=thumbnail)
            embed.add_field(name="Prénom", value=answers["prénom"], inline=True)
            embed.add_field(name="Âge", value=answers["âge"], inline=True)
            embed.add_field(name="Département", value=answers["département"], inline=True)
            embed.add_field(name="Genre", value=answers["genre"], inline=True)
            embed.add_field(name="Orientation", value=answers["orientation"], inline=True)
            embed.add_field(name="Recherche sur le serveur", value=answers["recherche"], inline=False)
            embed.add_field(name="Recherche chez quelqu'un", value=answers["recherche_chez_autrui"], inline=False)
            embed.add_field(name="Passions", value=answers["passions"], inline=False)
            embed.add_field(name="Description", value=answers["description"], inline=False)

            # View avec boutons
            view = View()
            view.add_item(ContactButton(interaction.user.id))
            view.add_item(SignalButton(interaction.user.id))

            message = await channel.send(embed=embed, view=view)
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            presentation_authors[message.id] = interaction.user.id
            user_profiles[interaction.user.id] = embed

            await interaction.user.send("✅ Ton profil a bien été envoyé !")

        except Exception as e:
            await interaction.user.send(f"❌ Une erreur est survenue : {e}")
class ContactButton(Button):
    def __init__(self, target_user_id):
        super().__init__(label="Contacter cette personne", style=discord.ButtonStyle.success)
        self.target_user_id = target_user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.target_user_id:
            await interaction.response.send_message("❌ Tu ne peux pas te contacter toi-même.", ephemeral=True)
            return

        contact_clicks.setdefault(interaction.user.id, [])
        if self.target_user_id in contact_clicks[interaction.user.id]:
            await interaction.response.send_message("❌ Tu as déjà contacté ce profil.", ephemeral=True)
            return
        if len(contact_clicks[interaction.user.id]) >= 3:
            await interaction.response.send_message("❌ Limite de 3 contacts atteinte.", ephemeral=True)
            return

        contact_clicks[interaction.user.id].append(self.target_user_id)

        # Alerte pointeur
        sender_age = int(user_answers[interaction.user.id]["âge"])
        receiver_age = int(user_answers[self.target_user_id]["âge"])
        min_age = (sender_age / 2) + 7

        if receiver_age < min_age:
            log = bot.get_channel(LOG_CHANNEL_ID)
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            await interaction.response.send_message("🚨 Écart d’âge inhabituel, action bloquée.", ephemeral=True)
            await log.send(f"⚠️ [POINTEUR] `{interaction.user}` ({sender_age} ans) a tenté de contacter `{self.target_user_id}` ({receiver_age} ans) le {now}")
            return

        compat = calculate_compatibility(user_answers[interaction.user.id], user_answers[self.target_user_id])
        try:
            target = await bot.fetch_user(self.target_user_id)
            await target.send(f"📩 {interaction.user.name}#{interaction.user.discriminator} souhaite te contacter via ton profil.")
        except:
            pass

        log = bot.get_channel(LOG_CHANNEL_ID)
        time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        await log.send(f"📬 `{interaction.user}` a cliqué sur **Contacter** le profil de `{target}` à {time} — Compatibilité : {compat}%")
        await interaction.user.send(f"🔗 Tu es compatible à **{compat}%** avec ce profil.")
        await interaction.response.send_message("📨 Demande envoyée (si la personne a ses MP ouverts).", ephemeral=True)

class SignalButton(Button):
    def __init__(self, user_id):
        super().__init__(label="🚩 Signaler ce profil", style=discord.ButtonStyle.danger)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        log = bot.get_channel(LOG_CHANNEL_ID)
        await log.send(f"🚩 `{interaction.user}` a **signalé** le profil de `{self.user_id}` à {now}")
        await interaction.response.send_message("🚨 Profil signalé. Merci pour ta vigilance.", ephemeral=True)

class FormButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FormButton())

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    channel = bot.get_channel(ACCUEIL_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🖤 Bienvenue dans l'antre des âmes liées...",
            description="> Clique sur le bouton ci-dessous pour remplir ta présentation et rencontrer quelqu’un.",
            color=discord.Color.from_str("#000000")
        )
        embed.set_thumbnail(url=IMAGE_URL)
        await channel.send(embed=embed, view=FormButtonView())
bot.run(TOKEN)


