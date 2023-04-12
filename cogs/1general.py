import discord
from discord.ext import commands
from replit import db
import datetime
from globalData import getConfig, ticketCode

# Denotes this code as a class of commands under the name General and initializes it
class General(commands.Cog):
  def __init__(self, client):
    self.client = client

  # Command for displaying bot info
  @commands.command()
  async def botInfo(self, ctx):
    cfg = getConfig(ctx.guild.id)

    # Get the bot's user object
    botUser = self.client.user

    # Create the bot info embed and send it
    botInfoEmbed = discord.Embed(title=f"{botUser.name}:", color=cfg["generalColor"])
    botInfoEmbed.set_thumbnail  (url=botUser.avatar_url)
    botInfoEmbed.add_field(name="Version:", value=db["Bot Version"], inline=True)
    botInfoEmbed.add_field(name="Last Updated:", value=db["Update Date"], inline=True)
    botInfoEmbed.add_field(name="Last Restart:", value=db["Last Restart"], inline=True)
    botInfoEmbed.set_footer(text=f"Bot ID: {self.client.user.id}")
    await ctx.send(embed=botInfoEmbed)

  # Command for displaying bot info
  @commands.command()
  @commands.guild_only()
  async def serverInfo(self, ctx):
    cfg = getConfig(ctx.guild.id)
    
    # Find the number of members not inlcuding the number of bots
    memberCount = ctx.guild.member_count
    botCount = 0

    for member in ctx.guild.members:
      if member.bot:
        memberCount -= 1
        botCount += 1

    # Create and send the server info embed
    serverInfoEmbed = discord.Embed(title= ctx.guild.name + " Info:", color=cfg["generalColor"])
    serverInfoEmbed.set_thumbnail(url=ctx.guild.icon_url)
    serverInfoEmbed.add_field(name="Owner:", value=ctx.guild.owner.display_name, inline=True)
    serverInfoEmbed.add_field(name="Creation:", value=ctx.guild.created_at.strftime ("%m/%d/%y"), inline=True)

    if botCount > 1 or botCount == 0:
      serverInfoEmbed.add_field(name="Members:", value= str(memberCount) +  " users,  " + str(botCount) + " bots", inline=True)
    else:
      serverInfoEmbed.add_field(name="Members:", value= str(memberCount) +  " users,  " + str(botCount) + " bot", inline=True)

    serverInfoEmbed.set_footer(text=f"Server ID: {ctx.guild.id}")
    await ctx.send(embed=serverInfoEmbed)

  # User info command
  @commands.command()
  async def userInfo(self, ctx, *, user: discord.Member):
    if user.name != self.client.user.name:
      cfg = getConfig(ctx.guild.id)

      # Create a user info embed
      if str(user.color) != "#000000":
        userInfoEmbed = discord.Embed(title=user.name, color=user.color)
      else:
        userInfoEmbed = discord.Embed(title=user.name, color=cfg["generalColor"])
      
      userInfoEmbed.set_thumbnail(url=user.avatar_url)
      userInfoEmbed.add_field(name="Joined on:", value=user.joined_at.strftime("%m/%d/%y"), inline=True)
      userInfoEmbed.add_field(name="Registered on:", value=user.created_at.strftime("%m/%d/%y"), inline=True)

      # Determine the member's role (if any) and add it as a field to the embed
      powerRoles = ["Bots", "Owners", "Admins", "Mods", "Developers", "Testers"]

      if user.top_role.name not in powerRoles:
        userInfoEmbed.add_field(name="Server Role:", value="Member", inline=True)
      else:
        userInfoEmbed.add_field(name="Server Role:", value=user.top_role.name[:-1], inline=True)
      
      userInfoEmbed.set_footer(text=f"User ID: {user.id}")
      
      await ctx.send(embed=userInfoEmbed)
    else:
      await ctx.send("**You can't use the userInfo command on me!** Try the `;botInfo` command instead.")

  # Update info command
  @commands.command()
  async def updateInfo(self, ctx, *, version: str=None):
    # If a version is specified, ensure it is in a usable format. Otherwise, fetch info
    # for the latest update
    if version != None:
      # Process the string and return a usable version number
      version = version.lower()
      if version[:1] != "v":
        version = "v" + version
    else:
      with open("updates.txt", "r") as file:
        contents = file.readlines()
        version = contents[0].strip()
    
    # Begin processing the file
    with open("updates.txt", "r") as file:
      # Search the updates txt file to check if the update exists
      found = False
      line = 0
      contents = file.readlines()
      while (not found) and ((line + 1) != len(contents)):
        if contents[line].strip() == version:
          found = True
        line += 1

      # If the version exists, extract update info
      if found:
        infoLine = 1
        updateInfo = ""
        # Store update information
        while (contents[line] != "\n") and ((line + 1) != len(contents)):
          if infoLine == 1:
            updateDate = contents[line].strip()
          elif infoLine == 2:
            updateName = contents[line].strip()
          else:
            updateInfo = updateInfo + contents[line]
          
          infoLine += 1
          line += 1

    if found:
      await ctx.send(f"__**GlitchBot {version}:** {updateName}__ | Initial Release: {updateDate}\n{updateInfo}")
    else:
      await ctx.send("**Sorry, but that update cannot be found.** Please that the update exists and its version is properly formatted.")

  # Bug report command
  @commands.command()
  async def bugReport(self, ctx, *, bugDesc: str):
    cfg = getConfig(ctx.guild.id)

    # Get the correct information using the dev server IDs
    devServer = self.client.get_guild(822636962526789662)
    devChannel = devServer.get_channel(827709464144379945)
    devRole = devServer.get_role(823935541543960576)

    # Generate a code for this bug report ticket
    ticketNumber = ticketCode(db, 'Bug Report')

    # Create a bug report embed and send it
    bugReportEmbed = discord.Embed(title=f"Bug report from {ctx.guild.name}:", description=bugDesc, color=cfg["negativeColor"])
    bugReportEmbed.set_author(name=f"{ctx.message.author.name} has found a bug", icon_url=ctx.message.author.avatar_url)
    bugReportEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804187951529197628/bugreport.png")
    bugReportEmbed.set_footer(text=f"Report #{ticketNumber} made on {(datetime.datetime.now()).strftime('%x at %X')} during v{db['Bot Version']}")

    bugReportMessage = await devChannel.send(content=f"{devRole.mention}", embed=bugReportEmbed)

    dmChannel = await ctx.message.author.create_dm()
    await dmChannel.send(f"**The developers have received your report. Thanks for submitting the issue! ** If more information is needed, one of the developers may reach out to you. If so, your ticket number is #{ticketNumber}.")

    db[f"Bug Report #{ticketNumber}"] = bugReportMessage.id

  # Suggestion command
  @commands.command()
  async def suggest(self, ctx, *, suggestion: str):
    cfg = getConfig(ctx.guild.id)

    # Get the correct information using the dev server IDs
    devServer = self.client.get_guild(822636962526789662)
    devChannel = devServer.get_channel(827709464144379945)
    devRole = devServer.get_role(823935541543960576)

    # Generate a code for this suggestion ticket
    ticketNumber = ticketCode(db, 'Suggestion')

    # Create a suggestion embed and send it
    suggestionEmbed = discord.Embed(title=f"Suggestion from {ctx.guild.name}:", description=suggestion, color=cfg["positiveColor"])
    suggestionEmbed.set_author(name=f"{ctx.message.author.name} has a suggestion", icon_url=ctx.message.author.avatar_url)
    suggestionEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/809597548523552788/suggestion.png")
    suggestionEmbed.set_footer(text=f"Suggestion #{ticketNumber(db, 'Suggestion')} made on {(datetime.datetime.now()).strftime('%x at %X')} during v{db['Bot Version']}")

    suggestionMessage = await devChannel.send(content=f"{devRole.mention}", embed=suggestionEmbed)
    dmChannel = await ctx.message.author.create_dm()
    await dmChannel.send(f"**The developers have received your suggestion. Thanks for submitting your idea! ** If more information is needed, one of the developers may reach out to you. If so, your ticket number is #{ticketNumber}.")

    db[f"Suggestion #{ticketNumber}"] = suggestionMessage.id

async def setup(client):
  await client.add_cog(General(client))