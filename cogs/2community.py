import discord
from discord.ext import commands
from replit import db
import asyncio
import datetime
import json

# Store necessary info locally from the JSON file
with open('globalVars.json', 'r') as jsonFile:
  globalVars = json.load(jsonFile)

colors = {}
for color in globalVars["embedColors"]:
  colors[color["color"]] = int(color["hex"], 0)

channels = {}
for channel in globalVars["channelIDs"]:
  channels[channel["channel"]] = channel["ID"]

roles = {}
for role in globalVars["roleIDs"]:
  roles[role["role"]] = role["ID"]

emojis = {}
for emoji in globalVars["emojiIDs"]:
  emojis[emoji["emoji"]] = emoji["ID"]

# Function for removing punctuation from parts of db keys
def clearPunctuation(string):
  punctuation = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
  for character in string:
    if character in punctuation:
      string = string.replace(character, "")
  
  return string

# Denotes this code as a class of commands under the name Community and initializes it
class Community(commands.Cog):
  def __init__(self, client):
    self.client = client
    
    # Gives this cog the attributes needed for the auto help command.
    self.parameters = ["<userID> <name>", "<serverName>",
    "<name> <desc> <game> <time>", "<eventName>", "<eventName>",
    "<eventName> <time>"]

    self.shortDescs = ["Creates an invite link for a user.",
    "Creates an invite link for a server.", "Creates a new event.",
    "Cancels an event.", "Deletes an event.", "Reschedules an event."]

    self.longDescs = [
      "Opens a vote for mods and admins to approve your invitation. The vote will close after 10 minutes and will act according to the final results. If nobody votes or there is a majority approval, a 12-hour invite link will be sent to your DMs so you can send it to your friend. If the vote ends in a tie or has a majority disapproval, you will not receive an invite link.",
      "Opens a vote for mods and admins to approve your invitation. The vote will close after 10 minutes and will act according to the final results. If nobody votes or there is a majority approval, a 24 hour, 25 use limit invite link will be sent to your DMs so you can send it to your server. If the vote ends in a tie or has a majority disapproval, you will not receive an invite link.",
      "Pings everyone in an embed to the events channel and automatically adds RSVP reactions to get an idea of who will be participating in the event.",
      "Cancels the specified event and informs everyone of the cancellation in the event channel.",
      "Deletes the specified event but does not inform people of its removal.",
      "Pings everyone in an embed that indicates the event that has been rescheduled and the new time it's taking place."]

    self.paramDescs = [
      "`<userID>` The ID of a user obtained by right-clicking a user's avatar and selecting Copy ID.\n`<name>` The user's actual name so we know who they are.",
      "`<serverName>` The name of the server you'd be sending the invite link to.",
      "`<name>` The name of the event you are hosting.\n`<desc>` A brief description of the event.\n`<game>` The name of the game you will be playing.\n`<time>` The time the event will take place (including time zone).",
      "`<name>` The exact name of the event you wish to cancel.",
      "`<name>` The exact name of the event you wish to delete.",
      "`<name>` The exact name of the event you wish to reschedule.\n`<time>` The new time the event will take place (including time zone)."
    ]

    self.restrictions = ["Anyone", "Anyone", "Anyone", "Only the host of the event", "Only the host of the event or a member of power ", "Only the host of the event"]
  
  # Personal invite command
  @commands.command()
  async def invite(self, ctx, userID: int, name: str):
    try:
      # Ensure an invite isn't already pending for the user before proceeding
      user = await self.client.fetch_user(userID)
      if ((("Personal Invite Pending For " + str(user.id)) not in db) or (db["Personal Invite Pending For " +  str(user.id)] == False)) and (user not in ctx.guild.members):
        db["Personal Invite Pending For " + str(user.id)] = True

        # Let the user know their request is being processed
        await ctx.send(f"{ctx.message.author.mention}- **The mods have received your request.** An invite link will be sent to you as soon as it's approved.")

        # Get the correct information using the IDs from the two servers
        if ctx.guild.name == "GlitchBot's Home":
          modChannel = self.client.get_channel(channels["gbhMod"])
          joinChannel = self.client.get_channel(channels["gbhJoin"])
          yesEmoji = self.client.get_emoji(emojis["gbhYes"])
          noEmoji = self.client.get_emoji(emojis["gbhNo"])
          modRole = ctx.guild.get_role(roles["gbhMods"])
          adminRole = ctx.guild.get_role(roles["gbhAdminss"])
        elif ctx.guild.name == "Glitched Gaming":
          modChannel = self.client.get_channel(channels["ggMod"])
          joinChannel = self.client.get_channel(channels["ggJoin"])
          yesEmoji = self.client.get_emoji(emojis["ggYes"])
          noEmoji = self.client.get_emoji(emojis["ggNo"])
          modRole = ctx.guild.get_role(roles["ggMods"])
          adminRole = ctx.guild.get_role(roles["ggAdmins"])

        # Send a confirmation embed to the mod channel and add the reactions
        inviteConfirmEmbed = discord.Embed(title="React to approve or disapprove!", color=colors["GGpurple"])
        inviteConfirmEmbed.set_author(name=f"{ctx.message.author.display_name} wants to invite {user.name} ({name})", icon_url=ctx.message.author.avatar_url)
        inviteConfirmEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284828870410280/invitepending.png")
        inviteConfirmEmbed.set_footer(text="Confirmation will end in 10 minutes")

        confirmationMessage = await modChannel.send(content=f"**{modRole.mention} s and {adminRole.mention} s:**", embed=inviteConfirmEmbed)
        await confirmationMessage.add_reaction(yesEmoji)
        await confirmationMessage.add_reaction(noEmoji)

        # Wait before tallying up the results
        minutes = 10
        while minutes >= 1:
          await asyncio.sleep(60)
          inviteConfirmEmbed.set_footer(text=f"Confirmation will end in {minutes} minutes")
          minutes -= 1
          await confirmationMessage.edit(embed=inviteConfirmEmbed)

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
      
        initiator = ctx.message.author
      
        # React appropriately according to the final vote results
        if (approves == disapproves) and (approves > 1 and disapproves > 1):
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="There was a tie!", description=f"An invite will not be sent for {user.name}.", color=colors["GGpurple"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)

          # Inform the initiator of the final decision
          initiatorResultsEmbed = discord.Embed(title=f"Your invite for {user.name} resulted in a tie!", description="An invite will not be sent, but you may try inviting them again at any time!", color=colors["GGpurple"])
          initiatorResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
          await initiator.send(embed=initiatorResultsEmbed)

        elif (approves == 1 and disapproves == 1):
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Nobody responded!", description=f"An invite will be sent for {user.name}!", color=colors["GGpurple"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
          await modChannel.send(embed=modResultsEmbed)
        
          # Inform the initiator of the final decision
          invitationEmbed = discord.Embed(title=f"Your invite for {user.name} was auto-approved!", description="Send them this invite link!", color=colors["GGpurple"])
          invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
          invitationEmbed.set_footer(text="Link is one-time use and will expire in 12 hours.")

          # Generate a new invite link
          inviteUrl = (await joinChannel.create_invite(max_age=43200, max_uses=1, unique=True,reason=f"Auto-approved invite for {user.name}")).url
          await initiator.send(embed=invitationEmbed)
          await initiator.send(inviteUrl)

        elif approves > disapproves:
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Invite approved!", description=f"An invite will be sent for {user.name}!", color=colors["GGblue"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)
        
          # Inform the initiator of the final decision
          invitationEmbed = discord.Embed(title=f"Your invite for {user.name} was approved!", description="Send them this invite link!", color=colors["GGblue"])
          invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
          invitationEmbed.set_footer(text="Link is one-time use and will expire in 12 hours.")
          # Generate a new invite link
          inviteUrl = (await joinChannel.create_invite(max_age=43200, max_uses=1, unique=True,reason=f"Mod-approved invite for {user.name}")).url
          await initiator.send(embed=invitationEmbed)
          await initiator.send(inviteUrl)
      
        elif approves < disapproves:
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Invite not approved!", description=f"An invite will not be sent for {user.name}!", color=colors["GGred"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284827188756510/invitedisapproved.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)
        
          # Inform the initiator of the final decision
          initiatorResultsEmbed = discord.Embed(title=f"Your invite for {user.name} was not approved!", description="An invite will not be sent, but you may try inviting them again at any time!", color=colors["GGred"])
          initiatorResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284827188756510/invitedisapproved.png")
          await initiator.send(embed=initiatorResultsEmbed)

        db["Personal Invite Pending For " + str(user.id)] = False
      elif user == ctx.message.author:
        await ctx.send("**Sorry, but you can't invite yourself!**")
      elif user in ctx.guild.members:
        await ctx.send("**Sorry, but you can't invite someone who's already in the server!**")
      elif user in await ctx.guild.bans():
        await ctx.send("**Sorry, but you can't invite someone who's been banned!**")
      elif (db["Personal Invite Pending For " + str(user.id)] == True):
        await ctx.send(f"**Sorry, but an invite is already pending for {user.name}.** If an invite isn't sent within 10 minutes, you may try again.")
    except:
      pass

  # Server invite command
  @commands.command()
  async def massInvite(self, ctx, *, serverName: str):
    # Ensure an invite isn't already pending for the server before proceeding
    if (("Server Invite Pending For " + serverName.title()) not in db) or ((db["Server Invite Pending For " +  serverName.title()]) == False):
      db["Server Invite Pending For " + serverName.title()] = True

      # Let the user their request is being processed
      await ctx.send(f"{ctx.message.author.mention}- **The mods have received your request.** An invite link will be sent to you as soon as it's approved.")

      # Get the correct information using the IDs from the two servers
      if ctx.guild.name == "GlitchBot's Home":
        modChannel = self.client.get_channel(channels["gbhMod"])
        joinChannel = self.client.get_channel(channels["gbhJoin"])
        yesEmoji = self.client.get_emoji(emojis["gbhYes"])
        noEmoji = self.client.get_emoji(emojis["gbhNo"])
        modRole = ctx.guild.get_role(roles["gbhMods"])
        adminRole = ctx.guild.get_role(roles["gbhAdmins"])
      elif ctx.guild.name == "Glitched Gaming":
        modChannel = self.client.get_channel(channels["ggMod"])
        joinChannel = self.client.get_channel(channels["ggJoin"])
        yesEmoji = self.client.get_emoji(emojis["ggYes"])
        noEmoji = self.client.get_emoji(emojis["ggNo"])
        modRole = ctx.guild.get_role(roles["ggMods"])
        adminRole = ctx.guild.get_role(roles["ggAdmins"])

      # Send a confirmation embed to the mod channel and add the reactions
      inviteConfirmEmbed = discord.Embed(title="React to approve or disapprove!", color = colors["GGpurple"])
      inviteConfirmEmbed.set_author(name=f"{ctx.message.author.display_name} wants to invite the {serverName.title()} server", icon_url=ctx.message.author.avatar_url)
      inviteConfirmEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284828870410280/invitepending.png")
      inviteConfirmEmbed.set_footer(text="Confirmation will end in 10 minutes")

      confirmationMessage = await modChannel.send(content=f"**{modRole.mention} s and {adminRole.mention} s:**", embed=inviteConfirmEmbed)
      await confirmationMessage.add_reaction(yesEmoji)
      await confirmationMessage.add_reaction(noEmoji)

        # Wait before tallying up the results
      minutes = 10
      while minutes >= 1:
        await asyncio.sleep(60)
        inviteConfirmEmbed.set_footer(text=f"Confirmation will end in {minutes} minutes")
        minutes -= 1
        await confirmationMessage.edit(embed=inviteConfirmEmbed)

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
      
      initiator = ctx.message.author
      
      # React appropriately according to the final vote results
      if (approves == disapproves) and (approves > 1 and disapproves > 1):
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="There was a tie!", description=f"An invite will not be sent to the {serverName.title()} server.", color=colors["GGpurple"])
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
        modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
        modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
        await modChannel.send(embed=modResultsEmbed)

        # Inform the initiator of the final decision
        initiatorResultsEmbed = discord.Embed(title=f"Your invite for {serverName.title()} resulted in a tie!", description="An invite will not be sent, but you may try inviting the server again at any time!", color=colors["GGpurple"])
        initiatorResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
        await initiator.send(embed=initiatorResultsEmbed)

      elif (approves == 1 and disapproves == 1):
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="Nobody responded!", description=f"An invite will be sent for the {serverName.title()} server!", color=colors["GGpurple"])
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
        await modChannel.send(embed=modResultsEmbed)
        
        # Inform the initiator of the final decision
        invitationEmbed = discord.Embed(title=f"Your invite for {serverName.title()} was auto-approved!", description="Use this invite link to invite them!", color=colors["GGpurple"])
        invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
        invitationEmbed.set_footer(text="Link will expire in 24 hours.")

        # Generate a new invite link
        inviteUrl = (await joinChannel.create_invite(max_age=86400, max_uses=25,unique=True,reason=f"Auto-approved invite for the {serverName.title()}")).url
        await initiator.send(embed=invitationEmbed)
        await initiator.send(inviteUrl)

      elif approves > disapproves:
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="Invite approved!", description=f"An invite will be sent for the {serverName.title()} server!", color=colors["GGblue"])
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
        modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
        modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
        await modChannel.send(embed=modResultsEmbed)
        
        # Inform the initiator of the final decision
        invitationEmbed = discord.Embed(title=f"Your invite for {serverName.title()} was approved!", description="Use this link to invite them!", color=colors["GGblue"])
        invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
        invitationEmbed.set_footer(text="Link will expire in 12 hours.")

        # Generate a new invite link
        inviteUrl = (await joinChannel.create_invite(max_age=86400, max_uses=25,unique=True,reason=f"Auto-approved invite for the {serverName.title()}")).url
        await initiator.send(embed=invitationEmbed)
        await initiator.send(inviteUrl)
      
      elif approves < disapproves:
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="Invite not approved!", description=f"An invite will not be sent for the {serverName.title()} server!", color=colors["GGred"])
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284827188756510/invitedisapproved.png")
        modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
        modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
        await modChannel.send(embed=modResultsEmbed)
        
        # Inform the initiator of the final decision
        initiatorResultsEmbed = discord.Embed(title=f"Your invite for {serverName.title()} was not approved!", description="An invite will not be sent, but you may try inviting them again at any time!", color=colors["GGred"])
        initiatorResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284827188756510/invitedisapproved.png")
        await initiator.send(embed=initiatorResultsEmbed)

      db["Server Invite Pending For " + serverName.title()] = False
    elif (db["Server Invite Pending For " + serverName.title()] == True):
      await ctx.send(f"**Sorry, but an invite is already pending for {serverName.title()}.** If an invite isn't sent within 10 minutes, you may try again.")

  # Event creation command
  @commands.command()
  async def event(self, ctx, name: str, desc: str, game: str, startTime: str):
    # Get the correct information using the IDs from the two servers
    if ctx.guild.name == "GlitchBot's Home":
      eventChannel = self.client.get_channel(channels["gbhEvent"])
      yesEmoji = self.client.get_emoji(emojis["gbhYes"])
      maybeEmoji = self.client.get_emoji(emojis["gbhMaybe"])
      noEmoji = self.client.get_emoji(emojis["gbhNo"])
    elif ctx.guild.name == "Glitched Gaming":
      eventChannel = self.client.get_channel(channels["ggEvent"])
      yesEmoji = self.client.get_emoji(emojis["ggYes"])
      maybeEmoji = self.client.get_emoji(emojis["ggMaybe"])
      noEmoji = self.client.get_emoji(emojis["ggNo"])
    
    # Create the event embed, send it, set up the reactions, and store event info
    eventEmbed = discord.Embed(title=name, description=desc, color=colors["GGblue"])
    eventEmbed.set_author(name=f"{ctx.message.author.display_name} is hosting an event", icon_url=ctx.message.author.avatar_url)
    eventEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/805241983286247424/eventcreated.png")
    eventEmbed.add_field(name="Game:", value=game, inline=True)
    eventEmbed.add_field(name="Time:", value=startTime, inline=True)
    eventEmbed.set_footer(text="React below so we know who to expect!")

    eventMessage = await eventChannel.send(content="@everyone", embed=eventEmbed)
    await eventMessage.add_reaction(yesEmoji)
    await eventMessage.add_reaction(maybeEmoji)
    await eventMessage.add_reaction(noEmoji)

    name = clearPunctuation(name)
    db["ID For Event " + name] = eventMessage.id
    db["Host ID For Event " + name] = ctx.message.author.id

  # Event cancellation command
  @commands.command()
  async def cancelEvent(self, ctx, *, name: str):
    name = clearPunctuation(name)
    # Ensure the specified event exists and the cancellee is the host before proceeding
    if ((("ID For Event " + name) in db) and (ctx.message.author.id == db["Host ID For Event " + name])) and (db["ID For Event " + name] != None):
      # Get the correct information using the IDs from the two servers
      if ctx.guild.name == "GlitchBot's Home":
        eventChannel = self.client.get_channel(channels["gbhEvent"])
      elif ctx.guild.name == "Glitched Gaming":
        eventChannel = self.client.get_channel(channels["ggEvent"])
      
      # Create the event embed, send it, then remove the original event embed
      cancellationEmbed = discord.Embed(title=f"{name} has been cancelled!", description="Stay tuned for more events!", color=colors["GGred"])
      cancellationEmbed.set_author(name=f"{ctx.message.author.display_name} cancelled an event", icon_url=ctx.message.author.avatar_url)
      cancellationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/805280828153528330/eventcancelled.png")

      eventMessage = await eventChannel.fetch_message(db["ID For Event " + name])
      await eventMessage.delete()
      await eventChannel.send(content="@everyone", embed=cancellationEmbed)
      db["ID For Event " + name] = None
    elif ("ID For Event " + name) not in db:
      await ctx.send("**Sorry, but I can't find an event with that name!** Check that the event exists and you are spelling its name correctly.")
    elif db["ID For Event " + name] == None:
      await ctx.send("**Sorry, but that event has already been cancelled!**")
    elif ctx.message.author.id != db["Host ID For Event " + name]:
      host = self.client.get_user(db["Host ID For Event " + name])
      await ctx.send(f"**Sorry, but only the event host can cancel that event!** Please reach out to {host.display_name} to do so.")

  # Event deletion command
  @commands.command()
  async def deleteEvent(self, ctx, *, name: str):
    name = clearPunctuation(name)
    
    # Ensure the person deleting the event is either its host or a member of power
    hostOrMod = False
    if ctx.message.author.id == db["Host ID For Event " + name]:
      hostOrMod = True
    if (ctx.message.author.top_role.name == "Mods") or (ctx.message.author.top_role.name == "Admins" or ctx.message.author.top_role.name == "Owners"):
      hostOrMod = True
    
    if ((("ID For Event " + name) in db) and (db["ID For Event " + name] != None)) and hostOrMod:
      # Get the correct information using the IDs from the two servers
      if ctx.guild.name == "GlitchBot's Home":
        eventChannel = self.client.get_channel(channels["gbhEvent"])
      elif ctx.guild.name == "Glitched Gaming":
        eventChannel = self.client.get_channel(channels["ggEvent"])
      
      # Delete the original event embed and inform the user the action was performed
      eventMessage = await eventChannel.fetch_message(db["ID For Event " + name])
      await eventMessage.delete()
      await eventChannel.send(f"**{name} event was deleted.**")
      db["ID For Event " + name] = None
    elif ("ID For Event " + name) not in db:
      await ctx.send("**Sorry, but I can't find an event with that name!** Check that the event exists and you are spelling its name correctly.")
    elif db["ID For Event " + name] == None:
      await ctx.send("**Sorry, but that event has already been cancelled!**")
    elif not hostOrMod:
      await ctx.send("**Sorry, but only the event host or members of power can delete that event!**")

  # Event rescheduling command
  @commands.command()
  async def rescheduleEvent(self, ctx, name: str, startTime: str):
    name = clearPunctuation(name)
    
    # Ensure the person deleting the event is its host
    if ((("ID For Event " + name) in db) and (ctx.message.author.id == db["Host ID For Event " + name])) and (db["ID For Event " + name] != None):
      # Get the correct information using the IDs from the two servers
      if ctx.guild.name == "GlitchBot's Home":
        eventChannel = self.client.get_channel(channels["gbhEvent"])
      elif ctx.guild.name == "Glitched Gaming":
        eventChannel = self.client.get_channel(channels["ggEvent"])
      
      # Create a reschedule embed and send it
      rescheduleEmbed = discord.Embed(title=f"{name} has been rescheduled to {startTime}!", color=colors["GGpurple"])
      rescheduleEmbed.set_author(name=f"{ctx.message.author.display_name} rescheduled an event", icon_url=ctx.message.author.avatar_url)
      rescheduleEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/809591752926953504/eventrescheduled.png")

      await eventChannel.send(content="@everyone", embed=rescheduleEmbed)
    elif (("ID For Event " + name) not in db) or db["ID For Event " + name] == None:
      await ctx.send("**Sorry, but that event has either been cancelled or does not exist!**")
    elif ctx.message.author.id != db["Host ID For Event " + name]:
      host = self.client.get_user(db["Host ID For Event " + name])
      await ctx.send(f"**Sorry, but only the event host can reschedule that event!** Please reach out to {host.name} to do so.")

def setup(client):
  client.add_cog(Community(client))