import discord
from discord.ext import commands
from replit import db
import asyncio
import datetime
from globalData import clearPunctuation, getConfig

# Denotes this code as a class of commands under the name Community and initializes it
class Community(commands.Cog):
  def __init__(self, client):
    self.client = client
    
    # Reset all pending invites
    for pendingInvite in db.prefix("Personal Invite Pending For "):
      db[pendingInvite] = False
    
    for pendingInvite in db.prefix("Server Invite Pending For "):
      db[pendingInvite] = False
  
  # Personal invite command
  @commands.command()
  @commands.guild_only()
  async def invite(self, ctx, userID: int, name: str):
    try:
      # Ensure an invite isn't already pending for the user before proceeding
      user = await self.client.fetch_user(userID)
      cfg = getConfig(ctx.guild.id)
      key = ("Personal Invite Pending For " + str(ctx.guild.id) + "-" + str(user.id))
      if ((key not in db) or (db[key] == False)) and (user not in ctx.guild.members):
        db[key] = True

        # Obtain the necessary guild information
        modChannel = ctx.guild.get_channel(cfg["vipChannel"])
        joinChannel = ctx.guild.get_channel(cfg["joinChannel"])
        modRole = ctx.guild.get_role(cfg["modRole"])
        adminRole = ctx.guild.get_role(cfg["adminRole"])
        yesEmoji = await ctx.guild.fetch_emoji(cfg["yesEmoji"])
        noEmoji = await ctx.guild.fetch_emoji(cfg["noEmoji"])

        # Let the user know their request is being processed
        await ctx.send(f"{ctx.message.author.mention}- **The mods have received your request.** An invite link will be sent to you as soon as it's approved.")

        # Send a confirmation embed to the mod channel and add the reactions
        inviteConfirmEmbed = discord.Embed(title="React to approve or disapprove!", color=cfg["positiveColor"])
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
          modResultsEmbed = discord.Embed(title="There was a tie!", description=f"An invite will not be sent for {user.name}.", color=cfg["generalColor"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)

          # Inform the initiator of the final decision
          initiatorResultsEmbed = discord.Embed(title=f"Your invite for {user.name} resulted in a tie!", description="An invite will not be sent, but you may try inviting them again at any time!", color=cfg["generalColor"])
          initiatorResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
          await initiator.send(embed=initiatorResultsEmbed)

        elif (approves == 1 and disapproves == 1):
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Nobody responded!", description=f"An invite will be sent for {user.name}!", color=cfg["generalColor"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
          await modChannel.send(embed=modResultsEmbed)
        
          # Inform the initiator of the final decision
          invitationEmbed = discord.Embed(title=f"Your invite for {user.name} was auto-approved!", description="Send them this invite link!", color=cfg["generalColor"])
          invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
          invitationEmbed.set_footer(text="Link is one-time use and will expire in 12 hours.")

          # Generate a new invite link
          inviteUrl = (await joinChannel.create_invite(max_age=43200, max_uses=1, unique=True,reason=f"Auto-approved invite for {user.name}")).url
          await initiator.send(embed=invitationEmbed)
          await initiator.send(inviteUrl)

        elif approves > disapproves:
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Invite approved!", description=f"An invite will be sent for {user.name}!", color=cfg["positiveColor"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)
        
          # Inform the initiator of the final decision
          invitationEmbed = discord.Embed(title=f"Your invite for {user.name} was approved!", description="Send them this invite link!", color=cfg["positiveColor"])
          invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
          invitationEmbed.set_footer(text="Link is one-time use and will expire in 12 hours.")
          # Generate a new invite link
          inviteUrl = (await joinChannel.create_invite(max_age=43200, max_uses=1, unique=True,reason=f"Mod-approved invite for {user.name}")).url
          await initiator.send(embed=invitationEmbed)
          await initiator.send(inviteUrl)
      
        elif approves < disapproves:
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Invite not approved!", description=f"An invite will not be sent for {user.name}!", color=cfg["negativeColor"])
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284827188756510/invitedisapproved.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)
        
          # Inform the initiator of the final decision
          initiatorResultsEmbed = discord.Embed(title=f"Your invite for {user.name} was not approved!", description="An invite will not be sent, but you may try inviting them again at any time!", color=cfg["negativeColor"])
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
  @commands.guild_only()
  async def massInvite(self, ctx, *, serverName: str):
    # Ensure an invite isn't already pending for the server before proceeding
    cfg = getConfig(ctx.guild.id)
    key = ("Server Invite Pending For " + str(ctx.guild.id) + "-" + serverName.title())
    if (key not in db) or (db[key] == False):
      db[key] = True

      # Let the user their request is being processed
      await ctx.send(f"{ctx.message.author.mention}- **The mods have received your request.** An invite link will be sent to you as soon as it's approved.")

      # Obtain the necessary guild information
      modChannel = ctx.guild.get_channel(cfg["vipChannel"])
      joinChannel = ctx.guild.get_channel(cfg["joinChannel"])
      modRole = ctx.guild.get_role(cfg["modRole"])
      adminRole = ctx.guild.get_role(cfg["adminRole"])
      yesEmoji = await ctx.guild.fetch_emoji(cfg["yesEmoji"])
      noEmoji = await ctx.guild.fetch_emoji(cfg["noEmoji"])

      # Send a confirmation embed to the mod channel and add the reactions
      inviteConfirmEmbed = discord.Embed(title="React to approve or disapprove!", color = cfg["generalColor"])
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
        modResultsEmbed = discord.Embed(title="There was a tie!", description=f"An invite will not be sent to the {serverName.title()} server.", color=cfg["generalColor"])
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
        modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
        modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
        await modChannel.send(embed=modResultsEmbed)

        # Inform the initiator of the final decision
        initiatorResultsEmbed = discord.Embed(title=f"Your invite for {serverName.title()} resulted in a tie!", description="An invite will not be sent, but you may try inviting the server again at any time!", color=cfg["generalColor"])
        initiatorResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
        await initiator.send(embed=initiatorResultsEmbed)

      elif (approves == 1 and disapproves == 1):
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="Nobody responded!", description=f"An invite will be sent for the {serverName.title()} server!", color=cfg["generalColor"])
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
        await modChannel.send(embed=modResultsEmbed)
        
        # Inform the initiator of the final decision
        invitationEmbed = discord.Embed(title=f"Your invite for {serverName.title()} was auto-approved!", description="Use this invite link to invite them!", color=cfg["generalColor"])
        invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
        invitationEmbed.set_footer(text="Link will expire in 24 hours.")

        # Generate a new invite link
        inviteUrl = (await joinChannel.create_invite(max_age=86400, max_uses=25,unique=True,reason=f"Auto-approved invite for the {serverName.title()}")).url
        await initiator.send(embed=invitationEmbed)
        await initiator.send(inviteUrl)

      elif approves > disapproves:
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="Invite approved!", description=f"An invite will be sent for the {serverName.title()} server!", color=cfg["positiveColor"])
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
        modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
        modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
        await modChannel.send(embed=modResultsEmbed)
        
        # Inform the initiator of the final decision
        invitationEmbed = discord.Embed(title=f"Your invite for {serverName.title()} was approved!", description="Use this link to invite them!", color=cfg["positiveColor"])
        invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
        invitationEmbed.set_footer(text="Link will expire in 12 hours.")

        # Generate a new invite link
        inviteUrl = (await joinChannel.create_invite(max_age=86400, max_uses=25,unique=True,reason=f"Auto-approved invite for the {serverName.title()}")).url
        await initiator.send(embed=invitationEmbed)
        await initiator.send(inviteUrl)
      
      elif approves < disapproves:
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="Invite not approved!", description=f"An invite will not be sent for the {serverName.title()} server!", color=cfg["negativeColor"])
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284827188756510/invitedisapproved.png")
        modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
        modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
        await modChannel.send(embed=modResultsEmbed)
        
        # Inform the initiator of the final decision
        initiatorResultsEmbed = discord.Embed(title=f"Your invite for {serverName.title()} was not approved!", description="An invite will not be sent, but you may try inviting them again at any time!", color=cfg["negativeColor"])
        initiatorResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284827188756510/invitedisapproved.png")
        await initiator.send(embed=initiatorResultsEmbed)

      db["Server Invite Pending For " + serverName.title()] = False
    elif (db["Server Invite Pending For " + serverName.title()] == True):
      await ctx.send(f"**Sorry, but an invite is already pending for {serverName.title()}.** If an invite isn't sent within 10 minutes, you may try again.")

  # Event creation command
  @commands.command()
  @commands.guild_only()
  async def event(self, ctx, name: str, desc: str, game: str, startTime: str):
    cfg = getConfig(ctx.guild.id)
    
    # Obtain the necessary guild information
    eventChannel = ctx.guild.get_channel(cfg["eventChannel"])
    yesEmoji = self.client.get_emoji(cfg["yesEmoji"])
    noEmoji = self.client.get_emoji(cfg["noEmoji"])
    maybeEmoji = self.client.get_emoji(cfg["maybeEmoji"])
    
    # Create the event embed, send it, set up the reactions, and store event info
    eventEmbed = discord.Embed(title=name, description=desc, color=cfg["positiveColor"])
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
    keySuffix = str(ctx.guild.id) + "-" + name
    db["ID For Event " + keySuffix] = eventMessage.id
    db["Host ID For Event " + keySuffix] = ctx.message.author.id

  # Event cancellation command
  @commands.command()
  @commands.guild_only()
  async def cancelEvent(self, ctx, *, name: str):
    name = clearPunctuation(name)
    cfg = getConfig(ctx.guild.id)
    keySuffix = str(ctx.guild.id) + "-" + name

    # Ensure the specified event exists and the cancellee is the host before proceeding
    if ((("ID For Event " + keySuffix) in db) and (ctx.message.author.id == db["Host ID For Event " + keySuffix])) and (db["ID For Event " + keySuffix] != None):
      # Obtain the necessary guild information
      eventChannel = ctx.guild.get_channel(cfg["eventChannel"])
      
      # Create the event embed, send it, then remove the original event embed
      cancellationEmbed = discord.Embed(title=f"{name} has been cancelled!", description="Stay tuned for more events!", color=cfg["negativeColor"])
      cancellationEmbed.set_author(name=f"{ctx.message.author.display_name} cancelled an event", icon_url=ctx.message.author.avatar_url)
      cancellationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/805280828153528330/eventcancelled.png")

      eventMessage = await eventChannel.fetch_message(db["ID For Event " + keySuffix])
      await eventMessage.delete()
      await eventChannel.send(content="@everyone", embed=cancellationEmbed)
      
      # Delete event data from the database
      del db["ID For Event " + keySuffix]
      del db["Host ID For Event " + keySuffix]

    elif ("ID For Event " + keySuffix) not in db:
      await ctx.send("**Sorry, but I can't find an event with that name!** Check that the event exists and you are spelling its name correctly.")
    elif db["ID For Event " + keySuffix] == None:
      await ctx.send("**Sorry, but that event has already been cancelled!**")
    elif ctx.message.author.id != db["Host ID For Event " + keySuffix]:
      host = self.client.get_user(db["Host ID For Event " + keySuffix])
      await ctx.send(f"**Sorry, but only the event host can cancel that event!** Please reach out to {host.display_name} to do so.")

  # Event deletion command
  @commands.command()
  @commands.guild_only()
  async def deleteEvent(self, ctx, *, name: str):
    name = clearPunctuation(name)
    cfg = getConfig(ctx.guild.id)
    keySuffix = str(ctx.guild.id) + "-" + name

    # Ensure the person deleting the event is either its host or a member of power
    hostOrMod = False
    if ctx.message.author.id == db["Host ID For Event " + keySuffix]:
      hostOrMod = True
    if (ctx.message.author.top_role.id == cfg["modRole"]) or (ctx.message.author.top_role.id == cfg["adminRole"] or ctx.message.author.id == ctx.guild.owner_id):
      hostOrMod = True
    
    if ((("ID For Event " + keySuffix) in db) and (db["ID For Event " + keySuffix] != None)) and hostOrMod:

      # Obtain the necessary guild information
      eventChannel = ctx.guild.get_channel(cfg["eventChannel"])
      
      # Delete the original event embed and inform the user the action was performed
      eventMessage = await eventChannel.fetch_message(db["ID For Event " + keySuffix])
      await eventMessage.delete()
      await eventChannel.send(f"**{name} event was deleted.**")

      # Delete event data from the database
      del db["ID For Event " + keySuffix]
      del db["Host ID For Event " + keySuffix]
    elif ("ID For Event " + keySuffix) not in db:
      await ctx.send("**Sorry, but I can't find an event with that name!** Check that the event exists and you are spelling its name correctly.")
    elif db["ID For Event " + keySuffix] == None:
      await ctx.send("**Sorry, but that event has already been cancelled!**")
    elif not hostOrMod:
      await ctx.send("**Sorry, but only the event host or members of power can delete that event!**")

  # Event rescheduling command ---------------------------
  @commands.command()
  @commands.guild_only()
  async def rescheduleEvent(self, ctx, name: str, startTime: str):
    name = clearPunctuation(name)
    cfg = getConfig(ctx.guild.id)
    keySuffix = str(ctx.guild.id) + "-" + name
    
    # Ensure the person deleting the event is its host
    if ((("ID For Event " + keySuffix) in db) and (ctx.message.author.id == db["Host ID For Event " + keySuffix])) and (db["ID For Event " + keySuffix] != None):
      # Obtain the necessary guild information
      eventChannel = ctx.guild.get_channel(cfg["eventChannel"])
      
      # Create a reschedule embed and send it
      rescheduleEmbed = discord.Embed(title=f"{name} has been rescheduled to {startTime}!", color=cfg["generalColor"])
      rescheduleEmbed.set_author(name=f"{ctx.message.author.display_name} rescheduled an event", icon_url=ctx.message.author.avatar_url)
      rescheduleEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/809591752926953504/eventrescheduled.png")

      await eventChannel.send(content="@everyone", embed=rescheduleEmbed)
    elif (("ID For Event " + keySuffix) not in db) or db["ID For Event " + keySuffix] == None:
      await ctx.send("**Sorry, but that event has either been cancelled or does not exist!**")
    elif ctx.message.author.id != db["Host ID For Event " + keySuffix]:
      host = self.client.get_user(db["Host ID For Event " + keySuffix])
      await ctx.send(f"**Sorry, but only the event host can reschedule that event!** Please reach out to {host.name} to do so.")

async def setup(client):
  await client.add_cog(Community(client))