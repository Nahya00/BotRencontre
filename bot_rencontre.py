    guild = interaction.guild
    embed = discord.Embed(
        title="🕊️ Confession Anonyme",
        description=message,
        color=discord.Color.from_rgb(15, 15, 15)  # Noir très sombre
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.set_footer(text="Envoyé anonymement • Discord", icon_url=guild.icon.url if guild.icon else None)

