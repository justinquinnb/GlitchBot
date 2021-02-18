import discord
from discord.ext import commands
from replit import db
import asyncio

# Mod channels for use in invites
gbdModChannel = 796411226468122674
ggModChannel = 769259341249249330
gbdJoinChannel = 796452386461319248
ggJoinChannel = 795493452967968798

# GG colors for use in embeds
GGred=0xc81e4e
GGblue=0x1dc9bf
GGpurple=0x9a2ab0

# Ordinal function
def ordinal(num):
  number = str(num)
  lastDigit = number[-1:]
  if lastDigit == '0':
    numEnd = "th"
  elif lastDigit == '1':
    numEnd = "st"
  elif lastDigit == '2':
    numEnd = "nd"
  elif lastDigit == '3':
    numEnd = "rd"
  elif (float(lastDigit) <= 9) and (float(lastDigit) >= 4):
    numEnd = "th"
  
  return number + numEnd

# Denotes this code as a class of commands under the name General and initializes it
class Moderation(commands.Cog):
  def __init__(self, client):
    self.client = client

    # Gives this cog the attributes needed for the auto help command.
    self.parameters = ["<@user>", "<numOfMessages>", "<@user>", "<@user>", "<@user> <reason>"]
    self.descriptions = ["Allows mods to vote-ban a user.",
    "Deletes specified number of messages.",
    "Allows mods and admins to anonymously warn a user.",
    "Allows admins to reset a user's warnings.",
    "Allows anyone to report a user for a reason."]

    # Reset all pending bans
    for pendingBan in db.prefix("Ban Pending For "):
      db[pendingBan] = False
  
  # Check for mod level or above
  def isModOrAbove(ctx):
    return (((ctx.message.author.top_role.name == "Mods") or (ctx.message.author.top_role.name == "Admins"))) or (ctx.message.author.top_role.name == "Owners")

  # Check for admin level or above
  def isAdminOrAbove(ctx):
    return (ctx.message.author.top_role.name == "Admins") or (ctx.message.author.top_role.name == "Owners")

  # Ban command
  @commands.command()
  @commands.has_role("Mods")
  async def ban(self, ctx, user: discord.Member, reason: str):
    try:
      possible = True

      # A cleaner way to determine whether or not the ban is possible
      if ((user.top_role.name == "Mods") or ((user.top_role.name == "Admins") or (user.top_role.name == "Owners"))):
        possible = False
      
      if user not in ctx.guild.members:
        possible = False

      if user is ctx.message.author:
        possible = False
      
      if ((f"Ban Pending For {str(user.id)}") in db) and (db[f"Ban Pending For {str(user.id)}"] == True):
        possible = False

      if possible:
        db["Ban Pending For " + str(user.id)] = True

        # Let the user know their request is being processed
        await ctx.send(f"{ctx.message.author.mention}- **Request received.** The user will be banned if approved.")

        # Get the correct information using the IDs from the two servers
        if ctx.guild.name == "GlitchBot's Home":
          modChannel = self.client.get_channel(gbdModChannel)
          yesEmoji = self.client.get_emoji(802964584868085770)
          noEmoji = self.client.get_emoji(802964584683012137)
          modRole = ctx.guild.get_role(801301557093728265)
          adminRole = ctx.guild.get_role(801301846446178366)
        elif ctx.guild.name == "Glitched Gaming":
          modChannel = self.client.get_channel(ggModChannel)
          yesEmoji = self.client.get_emoji(779855811480387635)
          noEmoji = self.client.get_emoji(779855943130546196)
          modRole = ctx.guild.get_role(769175358779162647)
          adminRole = ctx.guild.get_role(769176118213083166)
        
        # Send a confirmation embed to the mod channel and add the reactions
        banConfirmEmbed = discord.Embed(title="React to approve or disapprove!", color = GGpurple)
        banConfirmEmbed.set_author(name=f"{ctx.message.author.name} wants to ban {user.name}", icon_url=ctx.message.author.avatar_url)
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

        if (approves == disapproves) and (approves > 1 and disapproves > 1):
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="There was a tie!", description=f"{user.name} will not be banned.", color=GGpurple)
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804384663728422952/memberbanautocontroversial.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)

        elif (approves == 1 and disapproves == 1):
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Nobody responded!", description=f"{user.name} will not be banned.", color=GGpurple)
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804384663728422952/memberbanautocontroversial.png")
          await modChannel.send(embed=modResultsEmbed)

        elif approves > disapproves:
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Ban approved!", description=f"{user.name} will be banned!", color=GGred)
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804385045095776316/memberbanapproved.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)
        
          # Ban the user
          await ctx.guild.ban(user, reason="Vote approved. Reason:" + reason)
      
        elif approves < disapproves:
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Ban not approved!", description=f"{user.name} will not be banned!", color=GGblue)
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804384084382056528/memberbandisapproved.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)

        db[f"Ban Pending {str(user.id)}"] = False
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
      if ctx.message.author.top_role.name == "Owners":
        if numOfMessages > 50:
          numOfMessages = 50
          await ctx.channel.purge(limit=numOfMessages)
          await ctx.send(f"**For safety purposes, max messages per purge is maxed at 50.** {ctx.message.author.name} deleted {numOfMessages} messages!")
        else:
          await ctx.channel.purge(limit=numOfMessages)
          await ctx.send(f"**{ctx.message.author.name} deleted {numOfMessages} messages!**")
      elif ctx.message.author.top_role.name == "Admins":
        if numOfMessages > 25:
          numOfMessages = 25
          await ctx.channel.purge(limit=numOfMessages)
          await ctx.send(f"**You may only purge up to 25 messages at a time as an admin.** {ctx.message.author.name} deleted 25 messages!.")
        else:
          await ctx.channel.purge(limit=numOfMessages)
          await ctx.send(f"**{ctx.message.author.name} deleted {numOfMessages} messages!**")
      elif ctx.message.author.top_role.name == "Mods":
        if numOfMessages > 10:  
          numOfMessages = 10
          await ctx.channel.purge(limit=numOfMessages)
          await ctx.send(f"**You may only purge up to 10 messages at a time as a mod.** {ctx.message.author.name} deleted 10 messages!")
        else:
          await ctx.channel.purge(limit=numOfMessages)
          await ctx.send(f"**{ctx.message.author.name} deleted {numOfMessages} messages!**")

    except:
      pass
  
  # Warn user command
  @commands.command()
  @commands.check(isModOrAbove)
  async def warn(self, ctx, user: discord.Member, reason: str):
    if ((user.top_role.name != "Mods") and (user.top_role.name != "Admins")) and user.top_role.name != "Owners":
      if ("Warnings For " + str(user.id)) not in db:
        db["Warnings For " + str(user.id)] = 1
      else:
        db["Warnings For " + str(user.id)] += 1
    
      # Create a warning embed and send it
      warningEmbed = discord.Embed(title="You've received a warning!", description=reason, color=GGred)
      warningEmbed.set_author(name=f"{ctx.guild.name} has sent you a warning", icon_url=ctx.guild.icon_url)
      warningEmbed.set_thumbnail(url="https://media.discordapp.net/attachments/796907538570412033/809585178032341032/warning.png")
      warningEmbed.set_footer(text=f"This is your {ordinal(db['Warnings For ' + str(user.id)])} warning!")

      await user.send(embed=warningEmbed)
      await ctx.send(f"**{user.name} has been warned!**")
    else:
      await ctx.send("**You can't warn another member of power!**")

  # Warn user command
  @commands.command()
  @commands.check(isAdminOrAbove)
  async def resetWarns(self, ctx, user: discord.Member):
    if ((user.top_role.name != "Mods") and (user.top_role.name != "Admins")) and user.top_role.name != "Owners":
      db["Warnings For " + str(user.id)] = 0
      await ctx.send(f"**{ctx.message.author.name} has reset {user.name}'s warnings!**")
    else:
      await ctx.send("**You can't reset another member of power's warnings as they can't be warned.**")

  # Report user command
  @commands.command()
  async def report(self, ctx, user: discord.Member, reason: str):
    if ((ctx.message.author.top_role.name != "Mods") and (ctx.message.author.top_role.name != "Admins")) and ctx.message.author.top_role.name != "Owners":
      # Create a report embed and send it to the mods channel
      reportEmbed = discord.Embed(title=f"{user.name} was reported for...", description=reason, color=GGred)
      reportEmbed.set_author(name=f"{ctx.message.author.name} made a report", icon_url=ctx.message.author.avatar_url)
      reportEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804537971994263592/warning.png")

      if ctx.guild.name == "Glitched Gaming":
        modRole = ctx.guild.get_role(769175358779162647)
        adminRole = ctx.guild.get_role(769176118213083166)
        modChannel = self.client.get_channel(ggModChannel)
      elif ctx.guild.name == "GlitchBot's Home":
        modRole = ctx.guild.get_role(801301557093728265)
        adminRole = ctx.guild.get_role(801301846446178366)
        modChannel = self.client.get_channel(gbdModChannel)
      
      await modChannel.send(content=f"**{modRole.mention} s and {adminRole.mention} s:**", embed=reportEmbed)
      response = await ctx.send(f"**{user.name} was reported to the mods!** This exchange will be deleted in 3 seconds.")

      await asyncio.sleep(3)
      await ctx.message.delete()
      await response.delete()
    else:
      await ctx.send("**You don't need to report another user, you have power!**")


def setup(client):
  client.add_cog(Moderation(client))