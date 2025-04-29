import discord
from discord.ext import commands
from discord.ui import View, Button
import os  # Pour récupérer le token depuis Railway

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")  # Utilisation sécurisée du token via variable d'environnement

# IDs des salons
ACCUEIL_CHANNEL_ID = 1362035171301527654  # comment-faire-des-rencontres
FILLE_CHANNEL_ID = 1362035175269077174
GARCON_CHANNEL_ID = 1362035179358781480

# Lien direct vers ton image Imgur corrigé
IMAGE_URL = "https://i.imgur.com/JhYYTYA.png"

# Associer message ID -> utilisateur
presentation_authors = {}

class FormButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FormButton())

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
                ("Quel est ton **âge** ?", "âge"),
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

                    if key == "genre":
                        genre = msg.content.strip().lower()
                        if genre in ["fille", "garçon", "garcon"]:
                            answers[key] = "Garçon" if genre.startswith("gar") else "Fille"
                            valid = True
                        else:
                            await interaction.user.send("❌ Merci de répondre uniquement **Fille** ou **Garçon** !")
                    else:
                        answers[key] = msg.content
                        valid = True

            genre = answers.get("genre", "").lower()

            # Création de l'embed
            if "fille" in genre:
                color = discord.Color.from_str("#FFC0CB")
                title = "Nouveau profil Fille ! 💖"
                channel = bot.get_channel(FILLE_CHANNEL_ID)
            else:
                color = discord.Color.from_str("#87CEFA")
                title = "Nouveau profil Garçon ! 💙"
                channel = bot.get_channel(GARCON_CHANNEL_ID)

            embed = discord.Embed(
                title=title,
                description=f"Voici la présentation de {interaction.user.mention} !",
                color=color
            )
            embed.add_field(name="Prénom", value=answers['prénom'], inline=True)
            embed.add_field(name="Âge", value=answers['âge'], inline=True)
            embed.add_field(name="Département", value=answers['département'], inline=True)
            embed.add_field(name="Genre", value=answers['genre'], inline=True)
            embed.add_field(name="Orientation", value=answers['orientation'], inline=True)
            embed.add_field(name="Recherche sur le serveur", value=answers['recherche'], inline=False)
            embed.add_field(name="Recherche chez quelqu'un", value=answers['recherche_chez_autrui'], inline=False)
            embed.add_field(name="Passions", value=answers['passions'], inline=False)
            embed.add_field(name="Description", value=answers['description'], inline=False)
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty)
            embed.set_image(url=IMAGE_URL)

            message = await channel.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")

            # Sauvegarde de l'auteur de la présentation
            presentation_authors[message.id] = interaction.user.id

            await interaction.user.send("Ta présentation a été envoyée avec succès ! 💖")

        except Exception as e:
            await interaction.user.send(f"Une erreur est survenue : {e}")

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    
    channel = bot.get_channel(ACCUEIL_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="💖 Fais des rencontres ici !",
            description="Bienvenue sur notre espace rencontre !\nClique sur le bouton ci-dessous pour remplir ta fiche et te présenter aux autres.\n\nQue l'amour ou l'amitié commence ! 💌",
            color=discord.Color.from_str("#FCE38A")
        )
        embed.set_thumbnail(url=channel.guild.icon.url if channel.guild.icon else discord.Embed.Empty)
        embed.set_image(url=IMAGE_URL)
        await channel.send(embed=embed, view=FormButtonView())

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message_id = reaction.message.id
    if message_id in presentation_authors:
        pass  # Plus de DM envoyés

bot.run(TOKEN)