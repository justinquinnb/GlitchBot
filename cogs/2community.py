import discord
from discord.ext import commands
from replit import db
import asyncio
import datetime

# Mod channels for use in invites
gbdModChannel = 796411226468122674
ggModChannel = 769259341249249330
gbdJoinChannel = 796452386461319248
ggJoinChannel = 795493452967968798
gbdEventChannel = 796452386461319248
ggEventChannel = 769040700976136242

# GG colors for use in embeds
GGred=0xc81e4e
GGblue=0x1dc9bf
GGpurple=0x9a2ab0

# Denotes this code as a class of commands under the name Community and initializes it
class Community(commands.Cog):
  def __init__(self, client):
    self.client = client
    
    # Gives this cog the attributes needed for the auto help command.
    self.parameters = ["<userID> <name>", "<serverName>",
    "<name> <description> <game> <time>", "<eventName>", "<eventName>",
    "<eventName> <time>"]
    self.descriptions = ["Creates an invite link for a user.",
    "Creates an invite link for a server.", "Creates a new event.",
    "Cancels an event.", "Deletes an event.", "Reschedules an event."]
  
  # Personal invite command
  @commands.command()
  async def invite(self, ctx, userID: int, name: str):
    try:
      user = await self.client.fetch_user(userID)
      if ((("Personal Invite Pending For " + str(user.id)) not in db) or (db["Personal Invite Pending For " +  str(user.id)] == False)) and (user not in ctx.guild.members):
        db["Personal Invite Pending For " + str(user.id)] = True

        # Let the user know their request is being processed
        await ctx.send(f"{ctx.message.author.mention}- **The mods have received your request.** An invite link will be sent to you as soon as it's approved.")

        # Get the correct information using the IDs from the two servers
        if ctx.guild.name == "GlitchBot's Home":
          modChannel = self.client.get_channel(gbdModChannel)
          joinChannel = self.client.get_channel(gbdJoinChannel)
          yesEmoji = self.client.get_emoji(802964584868085770)
          noEmoji = self.client.get_emoji(802964584683012137)
          modRole = ctx.guild.get_role(801301557093728265)
          adminRole = ctx.guild.get_role(801301846446178366)
        elif ctx.guild.name == "Glitched Gaming":
          modChannel = self.client.get_channel(ggModChannel)
          joinChannel = self.client.get_channel(ggJoinChannel)
          yesEmoji = self.client.get_emoji(779855811480387635)
          noEmoji = self.client.get_emoji(779855943130546196)
          modRole = ctx.guild.get_role(769175358779162647)
          adminRole = ctx.guild.get_role(769176118213083166)

        # Send a confirmation embed to the mod channel and add the reactions
        inviteConfirmEmbed = discord.Embed(title="React to approve or disapprove!", color = GGpurple)
        inviteConfirmEmbed.set_author(name=f"{ctx.message.author.name} wants to invite {user.name} ({name})", icon_url=ctx.message.author.avatar_url)
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
      
        if (approves == disapproves) and (approves > 1 and disapproves > 1):
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="There was a tie!", description=f"An invite will not be sent for {user.name}.", color=GGpurple)
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)

          # Inform the initiator of the final decision
          initiatorResultsEmbed = discord.Embed(title=f"Your invite for {user.name} resulted in a tie!", description="An invite will not be sent, but you may try inviting them again at any time!", color=GGpurple)
          initiatorResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
          await initiator.send(embed=initiatorResultsEmbed)

        elif (approves == 1 and disapproves == 1):
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Nobody responded!", description=f"An invite will be sent for {user.name}!", color=GGpurple)
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
          await modChannel.send(embed=modResultsEmbed)
        
          # Inform the initiator of the final decision
          invitationEmbed = discord.Embed(title=f"Your invite for {user.name} was auto-approved!", description="Send them this invite link!", color=GGpurple)
          invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
          invitationEmbed.set_footer(text="Link is one-time use and will expire in 12 hours.")

          # Generate a new invite link
          inviteUrl = (await joinChannel.create_invite(max_age=43200, max_uses=1, unique=True,reason=f"Auto-approved invite for {user.name}")).url
          await initiator.send(embed=invitationEmbed)
          await initiator.send(inviteUrl)

        elif approves > disapproves:
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Invite approved!", description=f"An invite will be sent for {user.name}!", color=GGblue)
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)
        
          # Inform the initiator of the final decision
          invitationEmbed = discord.Embed(title=f"Your invite for {user.name} was approved!", description="Send them this invite link!", color=GGblue)
          invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
          invitationEmbed.set_footer(text="Link is one-time use and will expire in 12 hours.")
          # Generate a new invite link
          inviteUrl = (await joinChannel.create_invite(max_age=43200, max_uses=1, unique=True,reason=f"Mod-approved invite for {user.name}")).url
          await initiator.send(embed=invitationEmbed)
          await initiator.send(inviteUrl)
      
        elif approves < disapproves:
          # Inform the mods of the final decision using an embed
          modResultsEmbed = discord.Embed(title="Invite not approved!", description=f"An invite will not be sent for {user.name}!", color=GGred)
          modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284827188756510/invitedisapproved.png")
          modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
          modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
          await modChannel.send(embed=modResultsEmbed)
        
          # Inform the initiator of the final decision
          initiatorResultsEmbed = discord.Embed(title=f"Your invite for {user.name} was not approved!", description="An invite will not be sent, but you may try inviting them again at any time!", color=GGred)
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
    if (("Server Invite Pending For " + serverName.title()) not in db) or ((db["Server Invite Pending For " +  serverName.title()]) == False):
      db["Server Invite Pending For " + serverName.title()] = True

      # Let the user their request is being processed
      await ctx.send(f"{ctx.message.author.mention}- **The mods have received your request.** An invite link will be sent to you as soon as it's approved.")

      # Get the correct information using the IDs from the two servers
      if ctx.guild.name == "GlitchBot's Home":
        modChannel = self.client.get_channel(gbdModChannel)
        joinChannel = self.client.get_channel(gbdJoinChannel)
        yesEmoji = self.client.get_emoji(802964584868085770)
        noEmoji = self.client.get_emoji(802964584683012137)
        modRole = ctx.guild.get_role(801301557093728265)
        adminRole = ctx.guild.get_role(801301846446178366)
      elif ctx.guild.name == "Glitched Gaming":
        modChannel = self.client.get_channel(ggModChannel)
        joinChannel = self.client.get_channel(ggJoinChannel)
        yesEmoji = self.client.get_emoji(779855811480387635)
        noEmoji = self.client.get_emoji(779855943130546196)
        modRole = ctx.guild.get_role(769175358779162647)
        adminRole = ctx.guild.get_role(769176118213083166)

      # Send a confirmation embed to the mod channel and add the reactions
      inviteConfirmEmbed = discord.Embed(title="React to approve or disapprove!", color = GGpurple)
      inviteConfirmEmbed.set_author(name=f"{ctx.message.author.name} wants to invite the {serverName.title()} server", icon_url=ctx.message.author.avatar_url)
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
      
      if (approves == disapproves) and (approves > 1 and disapproves > 1):
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="There was a tie!", description=f"An invite will not be sent to the {serverName.title()} server.", color=GGpurple)
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
        modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
        modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
        await modChannel.send(embed=modResultsEmbed)

        # Inform the initiator of the final decision
        initiatorResultsEmbed = discord.Embed(title=f"Your invite for {serverName.title()} resulted in a tie!", description="An invite will not be sent, but you may try inviting the server again at any time!", color=GGpurple)
        initiatorResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284824822382633/invitecontroversial.png")
        await initiator.send(embed=initiatorResultsEmbed)

      elif (approves == 1 and disapproves == 1):
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="Nobody responded!", description=f"An invite will be sent for the {serverName.title()} server!", color=GGpurple)
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
        await modChannel.send(embed=modResultsEmbed)
        
        # Inform the initiator of the final decision
        invitationEmbed = discord.Embed(title=f"Your invite for {serverName.title()} was auto-approved!", description="Use this invite link to invite them!", color=GGpurple)
        invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780487453736990/inviteautoapproved.png")
        invitationEmbed.set_footer(text="Link will expire in 24 hours.")

        # Generate a new invite link
        inviteUrl = (await joinChannel.create_invite(max_age=86400, max_uses=25,unique=True,reason=f"Auto-approved invite for the {serverName.title()}")).url
        await initiator.send(embed=invitationEmbed)
        await initiator.send(inviteUrl)

      elif approves > disapproves:
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="Invite approved!", description=f"An invite will be sent for the {serverName.title()} server!", color=GGblue)
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
        modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
        modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
        await modChannel.send(embed=modResultsEmbed)
        
        # Inform the initiator of the final decision
        invitationEmbed = discord.Embed(title=f"Your invite for {serverName.title()} was approved!", description="Use this link to invite them!", color=GGblue)
        invitationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803780490255532042/inviteapproved.png")
        invitationEmbed.set_footer(text="Link will expire in 12 hours.")

        # Generate a new invite link
        inviteUrl = (await joinChannel.create_invite(max_age=86400, max_uses=25,unique=True,reason=f"Auto-approved invite for the {serverName.title()}")).url
        await initiator.send(embed=invitationEmbed)
        await initiator.send(inviteUrl)
      
      elif approves < disapproves:
        # Inform the mods of the final decision using an embed
        modResultsEmbed = discord.Embed(title="Invite not approved!", description=f"An invite will not be sent for the {serverName.title()} server!", color=GGred)
        modResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284827188756510/invitedisapproved.png")
        modResultsEmbed.add_field(name="Approves:", value=approves-1, inline=True)
        modResultsEmbed.add_field(name="Disapproves:", value=disapproves-1, inline=True)
        await modChannel.send(embed=modResultsEmbed)
        
        # Inform the initiator of the final decision
        initiatorResultsEmbed = discord.Embed(title=f"Your invite for {serverName.title()} was not approved!", description="An invite will not be sent, but you may try inviting them again at any time!", color=GGred)
        initiatorResultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/803284827188756510/invitedisapproved.png")
        await initiator.send(embed=initiatorResultsEmbed)

      db["Server Invite Pending For " + serverName.title()] = False
    elif (db["Server Invite Pending For " + serverName.title()] == True):
      await ctx.send(f"**Sorry, but an invite is already pending for {serverName.title()}.** If an invite isn't sent within 10 minutes, you may try again.")

  # Event creation command
  @commands.command()
  async def event(self, ctx, name: str, desc: str, game: str, startTime: str):
    if ctx.guild.name == "GlitchBot's Home":
      eventChannel = self.client.get_channel(gbdEventChannel)
      yesEmoji = self.client.get_emoji(802964584868085770)
      maybeEmoji = self.client.get_emoji(805245198686879804)
      noEmoji = self.client.get_emoji(802964584683012137)
    elif ctx.guild.name == "Glitched Gaming":
      eventChannel = self.client.get_channel(ggEventChannel)
      joinChannel = self.client.get_channel(ggJoinChannel)
      yesEmoji = self.client.get_emoji(779855811480387635)
      maybeEmoji = self.client.get_emoji(779856557432504330)
      noEmoji = self.client.get_emoji(779855943130546196)
    
    eventEmbed = discord.Embed(title=name, description=desc, color=GGblue)
    eventEmbed.set_author(name=f"{ctx.message.author.display_name} is hosting an event", icon_url=ctx.message.author.avatar_url)
    eventEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/805241983286247424/eventcreated.png")
    eventEmbed.add_field(name="Game:", value=game, inline=True)
    eventEmbed.add_field(name="Time:", value=startTime, inline=True)
    eventEmbed.set_footer(text="React below so we know who to expect!")

    eventMessage = await eventChannel.send(content="@everyone", embed=eventEmbed)
    await eventMessage.add_reaction(yesEmoji)
    await eventMessage.add_reaction(maybeEmoji)
    await eventMessage.add_reaction(noEmoji)
    db["ID For Event " + name] = eventMessage.id
    db["Host ID For Event " + name] = ctx.message.author.id

  # Event cancellation command
  @commands.command()
  async def cancelEvent(self, ctx, *, name: str):
    if ((("ID For Event " + name) in db) and (ctx.message.author.id == db["Host ID For Event " + name])) and (db["ID For Event " + name] != None):
      if ctx.guild.name == "GlitchBot's Home":
        eventChannel = self.client.get_channel(gbdEventChannel)
      elif ctx.guild.name == "Glitched Gaming":
        eventChannel = self.client.get_channel(ggEventChannel)
      
      cancellationEmbed = discord.Embed(title=f"{name} has been cancelled!", description="Stay tuned for more events!", color=GGred)
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
      await ctx.send(f"**Sorry, but only the event host can cancel that event!** Please reach out to {host.name} to do so.")

  # Event deletion command
  @commands.command()
  async def deleteEvent(self, ctx, *, name: str):
    hostOrMod = False

    if ctx.message.author.id == db["Host ID For Event " + name]:
      hostOrMod = True
    
    if (ctx.message.author.top_role.name == "Mods") or (ctx.message.author.top_role.name == "Admins" or ctx.message.author.top_role.name == "Owners"):
      hostOrMod = True
    
    if ((("ID For Event " + name) in db) and (db["ID For Event " + name] != None)) and hostOrMod:
      if ctx.guild.name == "GlitchBot's Home":
        eventChannel = self.client.get_channel(gbdEventChannel)
      elif ctx.guild.name == "Glitched Gaming":
        eventChannel = self.client.get_channel(ggEventChannel)
      
      eventMessage = await eventChannel.fetch_message(db["ID For Event " + name])
      await eventMessage.delete()
      await eventChannel.send(f"**{name} event was deleted.**")
      db["ID For Event " + name] = None
    elif ("ID For Event " + name) not in db:
      await ctx.send("**Sorry, but I can't find an event with that name!** Check that the event exists and you are spelling its name correctly.")
    elif db["ID For Event " + name] == None:
      await ctx.send("**Sorry, but that event has already been cancelled!**")
    elif not hostOrMod:
      await ctx.send("**Sorry, but only the event host or mods can delete that event!**")

  # Event rescheduling command
  @commands.command()
  async def rescheduleEvent(self, ctx, name: str, startTime: str):
    if ((("ID For Event " + name) in db) and (ctx.message.author.id == db["Host ID For Event " + name])) and (db["ID For Event " + name] != None):
      if ctx.guild.name == "GlitchBot's Home":
        eventChannel = self.client.get_channel(gbdEventChannel)
      elif ctx.guild.name == "Glitched Gaming":
        eventChannel = self.client.get_channel(ggEventChannel)
      
      rescheduleEmbed = discord.Embed(title=f"{name} has been rescheduled to {startTime}!", color=GGpurple)
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