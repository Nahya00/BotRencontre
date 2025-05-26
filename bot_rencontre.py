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
user_answers = {}
contact_clicks = {}

def calculate_compatibility(answers1, answers2):
    keys = ['genre', 'orientation', 'recherche', 'recherche_chez_autrui', 'passions']
    matches = sum(1 for key in keys if key in answers1 and key in answers2 and answers1[key].lower() == answers2[key].lower())
    return int((matches / len(keys)) * 100)

class ContactButton(Button):
    def __init__(self):
        super().__init__(label="Contacter cette personne", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        profil_message_id = interaction.message.id
        profil_owner_id = presentation_authors.get(profil_message_id)

        if not profil_owner_id or profil_owner_id not in user_profiles:
            await interaction.response.send_message("❌ Impossible de trouver les données du profil.", ephemeral=True)
            return

        if profil_owner_id == interaction.user.id:
            await interaction.response.send_message("❌ Tu ne peux pas contacter ton propre profil !", ephemeral=True)
            return

        sender_id = interaction.user.id
        receiver_id = profil_owner_id

        if sender_id not in contact_clicks:
            contact_clicks[sender_id] = []

        if receiver_id in contact_clicks[sender_id]:
            await interaction.response.send_message("❌ Tu as déjà tenté de contacter cette personne.", ephemeral=True)
            return

        if len(contact_clicks[sender_id]) >= 3:
            await interaction.response.send_message("❌ Tu as atteint la limite de 3 contacts.", ephemeral=True)
            return

        contact_clicks[sender_id].append(receiver_id)

        sender_data = user_profiles.get(sender_id)
        receiver_data = user_profiles.get(receiver_id)

        if not sender_data or not receiver_data:
            await interaction.response.send_message("❌ Données de profil incomplètes.", ephemeral=True)
            return

        sender_answers = sender_data["answers"]
        receiver_answers = receiver_data["answers"]

        sender_age = int(sender_answers.get("âge", 0))
        receiver_age = int(receiver_answers.get("âge", 0))

        min_allowed = (receiver_age / 2) + 7
        if sender_age < min_allowed:
            await interaction.response.send_message("❌ Ton âge est trop éloigné de celui de cette personne. Merci de respecter autrui.", ephemeral=True)
            log_channel = bot.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(f"⚠️ Tentative contact refusée entre {interaction.user.name}#{interaction.user.discriminator} ({sender_age}) et {receiver_answers['prénom']} ({receiver_age}) — Écart inacceptable.")
            return

        compatibility = calculate_compatibility(sender_answers, receiver_answers)
        try:
            await bot.get_user(receiver_id).send(
                f"📩 {interaction.user.name}#{interaction.user.discriminator} souhaite te contacter !\nCompatibilité : {compatibility}% {'💘 Très bonne compatibilité !' if compatibility >= 90 else '⚠️ Faible compatibilité'}"
            )
            await interaction.user.send("✅ Ta demande a été envoyée avec succès !")
        except:
            await interaction.response.send_message("❌ Je n'ai pas pu envoyer de message privé.", ephemeral=True)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            await log_channel.send(
                f"📩 {interaction.user.name}#{interaction.user.discriminator} a cliqué sur le bouton de contact du profil de {receiver_answers['prénom']}#{bot.get_user(receiver_id).discriminator if bot.get_user(receiver_id) else '?'} à {now}\nCompatibilité : {compatibility}% {'💘 Très bonne compatibilité !' if compatibility >= 90 else '⚠️ Faible compatibilité'}"
            )

class ReportButton(Button):
    def __init__(self):
        super().__init__(label="Signaler ce profil", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("🚨 Fonction de signalement simulée pour ce test.", ephemeral=True)

class ProfilButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ContactButton())
        self.add_item(ReportButton())

class FormButton(Button):
    def __init__(self):
        super().__init__(label="Remplir ma présentation", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("📩 Je t’ai envoyé un message privé pour remplir ton profil !", ephemeral=True)

        def check(m): return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

        try:
            questions = [
                ("📸 Veux-tu ajouter une photo ? (image ou lien, ou écris `skip`)", "photo"),
                ("Quel est ton prénom ?", "prénom"),
                ("Quel est ton âge ? (entre 15 et 35)", "âge"),
                ("Dans quel département vis-tu ?", "département"),
                ("Quel est ton genre ? (Fille / Garçon)", "genre"),
                ("Quelle est ton orientation ? (Hétéro / Homo / Bi / Pan / Autre)", "orientation"),
                ("Que recherches-tu ici ?", "recherche"),
                ("Qu’attends-tu chez quelqu’un ?", "recherche_chez_autrui"),
                ("Tes passions ?", "passions"),
                ("Petite description libre :", "description")
            ]

            answers = {}
            await interaction.user.send("**Remplissons ton profil ensemble !**")

            for question, key in questions:
                valid = False
                while not valid:
                    await interaction.user.send(question)
                    msg = await bot.wait_for("message", check=check, timeout=180)
                    content = msg.content.strip()

                    if key == "photo":
                        if msg.attachments:
                            answers[key] = msg.attachments[0].url
                            valid = True
                        elif content.startswith("http"):
                            answers[key] = content
                            valid = True
                        elif content.lower() == "skip":
                            answers[key] = IMAGE_URL
                            valid = True
                        else:
                            await interaction.user.send("❌ Envoie une image, un lien, ou écris `skip`.")
                    elif key == "âge":
                        if content.isdigit() and 15 <= int(content) <= 35:
                            answers[key] = content
                            valid = True
                        else:
                            await interaction.user.send("❌ Âge invalide. Entre un nombre entre 15 et 35.")
                    elif key == "genre":
                        if content.lower() in ["fille", "garçon", "garcon"]:
                            answers[key] = "Fille" if content.lower() == "fille" else "Garçon"
                            valid = True
                        else:
                            await interaction.user.send("❌ Réponds uniquement par 'Fille' ou 'Garçon'.")
                    else:
                        answers[key] = content
                        valid = True

            user_answers[interaction.user.id] = answers
            user_profiles[interaction.user.id] = {"answers": answers}

            is_fille = answers["genre"].lower() == "fille"
            title = "💖 Nouveau profil Fille !" if is_fille else "💙 Nouveau profil Garçon !"
            color = discord.Color.pink() if is_fille else discord.Color.blue()
            channel_id = FILLE_CHANNEL_ID if is_fille else GARCON_CHANNEL_ID
            channel = bot.get_channel(channel_id)

            embed = discord.Embed(
                title=title,
                description="❖ Un nouveau profil vient d'apparaître...\n\n> Il y a des regards qui racontent plus que mille mots.",
                color=color
            )
            embed.set_author(name=f"{interaction.user.name}#{interaction.user.discriminator}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            embed.set_thumbnail(url=answers["photo"])
            embed.add_field(name="Prénom", value=answers["prénom"], inline=True)
            embed.add_field(name="Âge", value=answers["âge"], inline=True)
            embed.add_field(name="Département", value=answers["département"], inline=True)
            embed.add_field(name="Genre", value=answers["genre"], inline=True)
            embed.add_field(name="Orientation", value=answers["orientation"], inline=True)
            embed.add_field(name="Recherche", value=answers["recherche"], inline=False)
            embed.add_field(name="Recherche chez quelqu’un", value=answers["recherche_chez_autrui"], inline=False)
            embed.add_field(name="Passions", value=answers["passions"], inline=False)
            embed.add_field(name="Description", value=answers["description"], inline=False)

            view = ProfilButtonView()
            message = await channel.send(embed=embed, view=view)
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            presentation_authors[message.id] = interaction.user.id

            log = bot.get_channel(LOG_CHANNEL_ID)
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            if log:
                await log.send(f"🆕 Nouveau profil créé par {interaction.user.name}#{interaction.user.discriminator} ({answers['âge']} ans) — {now}")

            await interaction.user.send("✅ Ton profil a bien été publié dans le salon !")

        except Exception as e:
            await interaction.user.send(f"❌ Une erreur s’est produite : {e}")

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
            description="> Viens glisser ton histoire parmi les regards silencieux.\n> Clique sur le bouton ci-dessous pour déposer ton profil, et laisse le destin s'en mêler.",
            color=discord.Color.dark_gray()
        )
        embed.set_thumbnail(url=IMAGE_URL)
        await channel.send(embed=embed, view=FormButtonView())

bot.run(TOKEN)

