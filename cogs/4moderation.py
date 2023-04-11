import discord
from discord.ext import commands
from replit import db
import asyncio
from globalData import ordinal, randomCode, getConfig

# Denotes this code as a class of commands under the name General and initializes it
class Moderation(commands.Cog):
  def __init__(self, client):
    self.client = client

    # Reset all pending bans
    for pendingBan in db.prefix("Ban Pending For "):
      db[pendingBan] = False
  
  # Custom config-compatible checks
  def isMod(ctx):
    cfg = getConfig(ctx.guild.id)
    return (ctx.message.author.top_role.id == cfg["modRole"])

  def isAdmin(ctx):
    cfg = getConfig(ctx.guild.id)
    return (ctx.message.author.top_role.id == cfg["adminRole"])

  def isModOrAbove(ctx):
    cfg = getConfig(ctx.guild.id)

    return (((ctx.message.author.top_role.id == cfg["modRole"]) or (ctx.message.author.top_role.id == cfg["adminRole"]))) or (ctx.message.author.id == ctx.guild.owner_id)

  def isAdminOrAbove(ctx):
    cfg = getConfig(ctx.guild.id)
    return (ctx.message.author.top_role.id == cfg["adminRole"]) or (ctx.message.author.id == ctx.guild.owner_id)

  # Ban command
  @commands.command()
  @commands.guild_only()
  @commands.check(isMod)
  async def ban(self, ctx, user: discord.Member, reason: str):
    try:
      possible = True

      # Determine if the ban is possible based on the banner and subject's roles
      if user is ctx.message.author:
        possible = False
      
      if user.name == self.client.user.name:
        possible = False
      
      key = "Ban Pending For " + str(ctx.guild.id) + "-" + str(user.id)

      if (key in db) and (db[key] == True):
        possible = False

      if possible:
        db[key] = True

        # Let the user know their request is being processed
        await ctx.send(f"{ctx.message.author.mention}- **Your ban request has been received.** The user will be banned if approved.")

        cfg = getConfig(ctx.guild.id)

        # Obtain the necessary guild information
        modChannel = ctx.guild.get_channel(cfg["vipChannel"])
        modRole = ctx.guild.get_role(cfg["modRole"])
        adminRole = ctx.guild.get_role(cfg["adminRole"])
        yesEmoji = await ctx.guild.fetch_emoji(cfg["yesEmoji"])
        noEmoji = await ctx.guild.fetch_emoji(cfg["noEmoji"])
        
        # Send a confirmation embed to the mod channel and add the reactions
        banConfirmEmbed = discord.Embed(title="React to approve or disapprove!", description=reason, color = cfg["generalColor"])
        banConfirmEmbed.set_author(name=f"{ctx.message.author.display_name} wants to ban {user.display_name}", icon_url=ctx.message.author.avatar_url)
        banConfirmEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804383266635382854/memberbanpending.png")
        banConfirmEmbed.set_footer(text="Confirmation will end in 30 minutes")

        confirmationMessage = await modChannel.send(content=f"**{modRole.mention} s and {adminRole.mention} s:**", embed=banConfirmEmbed)
        await confirmationMessage.add_reaction(yesEmoji)
        await confirmationMessage.add_reaction(noEmoji)

        # Wait before tallying up the results
        minutes = 30
        while minutes >= 1:
          await asyncio.sleep(60)
          banConfirmEmbed.set_footer(text=f"Confirmation will end in {minutes} minutes")
          minutes -= 1
          await confirmationMessage.edit(embed=banConfirmEmbed)

        await confirmationMessage.edit(content="**Confirmation ended!** Calculating results...")
        await confirmationMessage.edit(embed=None)

        # Cache the message
        confirmationMessage = await confirmationMessage.channel.fetch_message(confirmationMessage.id)

        # Tally up the reactions, then perform the appropriate response
        approves = 0
        disapproves = 0

        for reaction in confirmationMessage.reactions:
          if reaction.emoji == noEmoji:
            disapproves = reaction.count
          elif reaction.emoji == yesEmoji:
            approves = reaction.count

        # React appropriate according to the final vote results
        if (approves == disapproves) and (approves > 1 and disapproves > 1):
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="There was a tie!", description=f"{user.display_name} will not be banned.", color=cfg["generalColor"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804384663728422952/memberbanautocontroversial.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)

        elif (approves == 1 and disapproves == 1):
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Nobody responded!", description=f"{user.display_name} will not be banned.", color=cfg["generalColor"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804384663728422952/memberbanautocontroversial.png")
          await modChannel.send(embed=modResultsEmbed)

        elif approves > disapproves:
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Ban approved!", description=f"{user.display_name} will be banned!", color=cfg["negativeColor"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804385045095776316/memberbanapproved.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)
        
          # Ban the user
          await ctx.guild.ban(user, reason="Vote approved. Reason:" + reason)
      
        elif approves < disapproves:
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Ban not approved!", description=f"{user.display_name} will not be banned!", color=cfg["positiveColor"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804384084382056528/memberbandisapproved.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)

        del db[key]
      elif ctx.message.author == user:
        await ctx.send("**Sorry, but you can't ban yourself!**")
      elif db[f"Ban Pending For {user.name}"] == True:
        await ctx.send("**Sorry, but a ban is already pending for that user.** If the user isn't banned with 30 minutes, you may try again.")
      elif (user not in ctx.guild.members):
        await ctx.send("**Sorry, but you can't ban someone who's not in the server!**")
      elif ((user.top_role.name == "Mods") or ((user.top_role.name == "Admins") or (user.top_role.name == "Owners"))):
        await ctx.send("**Sorry, but you can't ban other members of power!**")
    except:
      pass
  
  # Purge messages command
  @commands.command()
  @commands.check(isModOrAbove)
  async def purge(self, ctx, numOfMessages: int):
    try:
      # Ensure the purge limits are enforced based on the user's highest role
      cfg = getConfig(ctx.guild.id)
      
      if ctx.message.author.id == ctx.guild.owner_id:
        if numOfMessages > 50:
          numOfMessages = 50
          await ctx.channel.purge(limit=numOfMessages + 1)
          await ctx.send(f"**For safety purposes, max messages per purge is maxed at 50.** {ctx.message.author.display_name} deleted {numOfMessages} messages!")
        else:
          await ctx.channel.purge(limit=numOfMessages + 1)
          await ctx.send(f"**{ctx.message.author.display_name} deleted {numOfMessages} messages!**")
      elif ctx.message.author.top_role.id == cfg["adminRole"]:
        if numOfMessages > 25:
          numOfMessages = 25
          await ctx.channel.purge(limit=numOfMessages + 1)
          await ctx.send(f"**You may only purge up to 25 messages at a time as an admin.** {ctx.message.author.display_name} deleted 25 messages!.")
        else:
          await ctx.channel.purge(limit=numOfMessages + 1)
          await ctx.send(f"**{ctx.message.author.display_name} deleted {numOfMessages} messages!**")
      elif ctx.message.author.top_role.id == cfg["modRole"]:
        if numOfMessages > 10:  
          numOfMessages = 10
          await ctx.channel.purge(limit=numOfMessages + 1)
          await ctx.send(f"**You may only purge up to 10 messages at a time as a mod.** {ctx.message.author.display_name} deleted 10 messages!")
        else:
          await ctx.channel.purge(limit=numOfMessages + 1)
          await ctx.send(f"**{ctx.message.author.display_name} deleted {numOfMessages} messages!**")

    except:
      pass
  
  # Warn user command
  @commands.command()
  @commands.guild_only()
  @commands.check(isModOrAbove)
  async def warn(self, ctx, user: discord.Member, reason: str):
    cfg = getConfig(ctx.guild.id)
    key = "Warnings For " + str(ctx.guild.id) + "-" + str(user.id)

    # Ensure the user is a member of power
    if ((user.top_role.id != cfg["modRole"]) and (user.top_role.id != cfg["adminRole"])) and user.id != ctx.guild.owner_id:
      # Increment and store the number of warnings for the specified user
      key = "Warning For " + str(ctx.guild.id) + "-" + str(user.id)
      if key not in db:
        db[key] = 1
      else:
        db[key] += 1
    
      # Create a warning embed and send it
      warningEmbed = discord.Embed(title="You've received a warning!", description=reason, color=cfg["negativeColor"])
      warningEmbed.set_author(name=f"{ctx.guild.name} has sent you a warning", icon_url=ctx.guild.icon_url)
      warningEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/816675512989515846/warning.png")
      warningEmbed.set_footer(text=f"This is your {ordinal(db[key])} warning!")

      await user.send(embed=warningEmbed)
      await ctx.send(f"**{user.display_name} has been warned!**")

      if db[key] >= 5:
        await ctx.send(f"**This is {user.display_name}'s {db[key]} warning!** Though not required, it may be time to consider further action.")
    else:
      await ctx.send("**You can't warn another member of power!**")

  # Warn user command
  @commands.command()
  @commands.guild_only()
  @commands.check(isAdminOrAbove)
  async def resetWarns(self, ctx, user: discord.Member):
    cfg = getConfig(ctx.guild.ig)
    key = "Warnings For " + str(ctx.guild.id) + "-" + str(user.id)

    # Ensure the user is a member of power and reset the specified user's warning count
    if ((user.top_role.id != cfg["modRole"]) and (user.top_role.id != cfg["adminRole"])) and user.id != ctx.guild.owner_id:
      db["Warnings For " + str(user.id)] = 0
      await ctx.send(f"**{ctx.message.author.display_name} has reset {user.display_name}'s warnings!**")
    else:
      await ctx.send("**You can't reset another member of power's warnings as they can't be warned.**")

  # Report user command
  @commands.command()
  @commands.guild_only()
  async def report(self, ctx, user: discord.Member, reason: str):
    cfg = getConfig(ctx.guild.id)
    
    # Determine the proper course-of-action based on who is being reported
    if (((user.top_role.id != cfg["modRole"]) and (user.top_role.id != cfg["adminRole"])) and user.id != ctx.guild.owner_id):
      # Create a report embed and send it to the mods channel
      reportEmbed = discord.Embed(title=f"{user.display_name} was reported for:", description=reason, color=cfg["negativeColor"])
      reportEmbed.set_author(name=f"{ctx.message.author.display_name} made a report", icon_url=ctx.message.author.avatar_url)
      reportEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/816675512989515846/warning.png")

      # Obtain the correct info from the guild config
      modRole = ctx.guild.get_role(cfg["modRole"])
      adminRole = ctx.guild.get_role(cfg["adminRole"])
      modChannel = self.client.get_channel(cfg["vipChannel"])
      
      await modChannel.send(content=f"**{modRole.mention} s and {adminRole.mention} s:**", embed=reportEmbed)
      response = await ctx.send(f"**{user.display_name} was reported to the mods!** This exchange will be deleted in 3 seconds.")

      await asyncio.sleep(3)
      await ctx.message.delete()
      await response.delete()
    else:
      # Create a report embed and send it to the owners
      reportEmbed = discord.Embed(title=f"{user.display_name} was reported in {ctx.guild.name} for:", description=reason, color=cfg["negativeColor"])
      reportEmbed.set_author(name=f"{ctx.message.author.display_name} made a report", icon_url=ctx.message.author.avatar_url)
      reportEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/816675512989515846/warning.png")
      
      justin = self.client.get_user(335440648393981952)
      jacob = self.client.get_user(456988979133284353)

      if not justin.dm_channel:
        await justin.create_dm()
      if not jacob.dm_channel:
        await jacob.create_dm()

      justinDM = justin.dm_channel
      jacobDM = jacob.dm_channel
      
      await justinDM.send(embed=reportEmbed)
      await jacobDM.send(embed=reportEmbed)
      response = await ctx.send(f"**{user.display_name} was reported to the owners!** This exchange will be deleted in 3 seconds.")

      await asyncio.sleep(3)
      await ctx.message.delete()
      await response.delete()

def setup(client):
  client.add_cog(Moderation(client))