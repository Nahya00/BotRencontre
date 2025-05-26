import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os
from datetime import datetime

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

GIRLS_CHANNEL_ID = 1362035175269077174  # à remplacer
BOYS_CHANNEL_ID = 1362035179358781480   # à remplacer
LOG_CHANNEL_ID = 1376347435747643475

PROFILE_FILE = "profils.json"
contact_cooldown = {}

if not os.path.exists(PROFILE_FILE):
    with open(PROFILE_FILE, "w") as f:
        json.dump({}, f)

def load_profiles():
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)

def save_profiles(data):
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def calculate_compatibility(user_data, target_data):
    total = 0
    match = 0
    for key in ["recherche", "recherche_chez", "passions"]:
        total += 1
        if user_data.get(key, "").lower() == target_data.get(key, "").lower():
            match += 1
    return round((match / total) * 100) if total > 0 else 0

def get_embed_color(gender):
    return discord.Color.blue() if gender.lower() == "garçon" else discord.Color.from_rgb(20, 20, 20)

class ProfileView(View):
    def __init__(self, user_id, image_url, embed_data):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.image_url = image_url
        self.embed_data = embed_data

    @discord.ui.button(label="Contacter cette personne", style=discord.ButtonStyle.success, custom_id="contact")
    async def contact(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_id = self.user_id
        sender = interaction.user

        profiles = load_profiles()
        target_data = profiles.get(str(target_id))
        sender_data = profiles.get(str(sender.id))

        if not target_data:
            return await interaction.response.send_message("Ce profil n'existe plus ou est incomplet.", ephemeral=True)

        # Vérif pointeur
        if sender_data:
            sender_age = int(sender_data.get("age", 0))
            target_age = int(target_data.get("age", 0))
            age_limit = (sender_age / 2) + 7
            if target_age < age_limit:
                now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
                await log_channel.send(f"⚠️ Alerte Pointeur : {sender.name}#{sender.discriminator} ({sender_age} ans) a tenté de contacter {target_data.get('prenom')} ({target_age} ans) à {now}")
                return await interaction.response.send_message("L'écart d'âge est inhabituel. Merci de respecter autrui.", ephemeral=True)

        compat_text = ""
        if sender_data and target_data:
            compat = calculate_compatibility(sender_data, target_data)
            if compat >= 90:
                compat_text = f" | Compatibilité : {compat}% ✅ (Très bonne compatibilité)"
            elif compat > 0:
                compat_text = f" | Compatibilité : {compat}% ⚠️ (Faible compatibilité)"

        try:
            await sender.send(f"Tu as demandé à contacter <@{target_id}>. Attends sa réponse !")
            await interaction.response.send_message("Ta demande a bien été envoyée.", ephemeral=True)

            try:
                await interaction.client.get_user(target_id).send(f"<@{sender.id}> veut te contacter !")
            except:
                pass

            log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            await log_channel.send(f"📨 {sender.name}#{sender.discriminator} a cliqué sur le bouton de contact du profil de {self.embed_data['author']['name']} à {now}{compat_text}")

        except:
            await interaction.response.send_message("Impossible de contacter cette personne.", ephemeral=True)

    @discord.ui.button(label="Signaler ce profil", style=discord.ButtonStyle.danger, custom_id="report")
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Le profil a été signalé. Merci pour votre vigilance.", ephemeral=True)

@bot.command()
async def publier(ctx):
    def check_author(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send("Quel est ton prénom ?")
    prenom = (await bot.wait_for("message", check=check_author)).content.strip()
    if len(prenom) < 2:
        return await ctx.send("Prénom trop court.")

    await ctx.send("Quel est ton âge ? (entre 15 et 35)")
    age_msg = await bot.wait_for("message", check=check_author)
    if not age_msg.content.isdigit():
        return await ctx.send("Âge invalide.")
    age = int(age_msg.content)
    if not 15 <= age <= 35:
        return await ctx.send("Âge hors limites autorisées.")

    await ctx.send("Ton département ?")
    departement = (await bot.wait_for("message", check=check_author)).content.strip()

    await ctx.send("Ton genre (Fille / Garçon) ?")
    genre = (await bot.wait_for("message", check=check_author)).content.strip()

    await ctx.send("Ton orientation ?")
    orientation = (await bot.wait_for("message", check=check_author)).content.strip()

    await ctx.send("Que recherches-tu sur ce serveur ?")
    recherche = (await bot.wait_for("message", check=check_author)).content.strip()

    await ctx.send("Que recherches-tu chez quelqu’un ?")
    recherche_chez = (await bot.wait_for("message", check=check_author)).content.strip()

    await ctx.send("Tes passions ?")
    passions = (await bot.wait_for("message", check=check_author)).content.strip()

    await ctx.send("Fais une petite description de toi :")
    description = (await bot.wait_for("message", check=check_author)).content.strip()

    await ctx.send("Envoie un lien ou une image, ou écris `skip`. Si tu veux, tu peux envoyer une **photo** en pièce jointe ou lien. Sinon, écris `skip`.")
    img_msg = await bot.wait_for("message", check=check_author)
    image_url = None
    if img_msg.attachments:
        image_url = img_msg.attachments[0].url
    elif img_msg.content.startswith("http"):
        image_url = img_msg.content

    embed = discord.Embed(
        title=f"{'💖' if genre.lower() == 'fille' else '💙'} Nouveau profil {'Fille' if genre.lower() == 'fille' else 'Garçon'} !",
        description="❖ Un nouveau profil vient d'apparaître...\n\n> Il y a des regards qui racontent plus que mille mots.",
        color=get_embed_color(genre)
    )
    embed.set_author(name=f"{ctx.author.name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    if image_url:
        embed.set_thumbnail(url=image_url)

    embed.add_field(name="Prénom", value=prenom, inline=False)
    embed.add_field(name="Âge", value=age, inline=False)
    embed.add_field(name="Département", value=departement, inline=False)
    embed.add_field(name="Genre", value=genre, inline=False)
    embed.add_field(name="Orientation", value=orientation, inline=False)
    embed.add_field(name="Recherche sur le serveur", value=recherche, inline=False)
    embed.add_field(name="Recherche chez quelqu’un", value=recherche_chez, inline=False)
    embed.add_field(name="Passions", value=passions, inline=False)
    embed.add_field(name="Description", value=description, inline=False)

    profiles = load_profiles()
    profiles[str(ctx.author.id)] = {
        "prenom": prenom,
        "age": age,
        "departement": departement,
        "genre": genre,
        "orientation": orientation,
        "recherche": recherche,
        "recherche_chez": recherche_chez,
        "passions": passions,
        "description": description
    }
    save_profiles(profiles)

    view = ProfileView(ctx.author.id, image_url, embed.to_dict())
    channel_id = GIRLS_CHANNEL_ID if genre.lower() == "fille" else BOYS_CHANNEL_ID
    target_channel = bot.get_channel(channel_id)
    await target_channel.send(embed=embed, view=view)
    await ctx.send("✅ Ton profil a bien été envoyé !")

bot.run("VOTRE_TOKEN")

