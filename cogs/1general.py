import discord
from discord.ext import commands
from replit import db
import datetime
import json

# Store necessary info locally from the JSON file
with open('globalVars.json', 'r') as jsonFile:
  globalVars = json.load(jsonFile)

colors = {}
for color in globalVars["embedColors"]:
  colors[color["color"]] = int(color["hex"], 0)

guilds = {}
for guild in globalVars["guildIDs"]:
  guilds[guild["guild"]] = guild["ID"]

channels = {}
for channel in globalVars["channelIDs"]:
  channels[channel["channel"]] = channel["ID"]

roles = {}
for role in globalVars["roleIDs"]:
  roles[role["role"]] = role["ID"]

# Denotes this code as a class of commands under the name General and initializes it
class General(commands.Cog):
  def __init__(self, client):
    self.client = client
    
    # Gives this cog the attributes needed for help command cataloguing
    self.parameters = ["", "", "<@user>", "(vX.X.X)", "<desc>", "<desc>"]

    self.shortDescs = ["Displays bot info.", "Displays server info.",
    "Displays user info.", "Displays update info.",
    "Report a bug to the GlitchBot devs.",
    "Suggest an idea to the GlitchBot devs."]

    self.longDescs = [
      "Displays an embed containing the bot's last restart, the date of its last update, its current version, and User ID.",
      "Displays an embed containing the names of the server's owner, the date of its creation, its Server ID, and its member count (including bots)",
      "Displays an embed containing the user's server join date, account registration date, server role, and User ID.",
      "Responds with the changelog of the specified update (or latest if none is included)",
      "Informs the developers of a bug via an embed on the GlitchBot development server.",
      "Suggests an idea to the developers via an embed on the GlitchBot development server."]

    self.paramDescs = [
      "", "", "`<@user>` Ping the desired user.",
      "`<vX.X.X>` A version number formatted as X.X.X where each X represents a number. Only required to retrieve info on a previous update.",
      "`<desc>` A description of the bug including what you did for it to happen and what the bot did as a response.",
      "`<desc>` A detailed description of your idea."]
    
    self.restrictions = ["Anyone", "Anyone", "Anyone", "Anyone", "Anyone", "Anyone"]

    # Reset all pending invites
    for pendingInvite in db.prefix("Personal Invite Pending For "):
      db[pendingInvite] = False
    
    for pendingInvite in db.prefix("Server Invite Pending For "):
      db[pendingInvite] = False

  # Command for displaying bot info
  @commands.command()
  async def botInfo(self, ctx):
    # Obtain bot update info
    with open("updates.txt", "r") as file:
      content = file.readlines()
      botVersion = content[0].strip()
      botUpdateDate = content[1].strip()

    # Create the bot info embed and send it
    botInfoEmbed = discord.Embed(title="BetaBot Info:", color=colors["GGpurple"])
    botInfoEmbed.set_thumbnail  (url="https://cdn.discordapp.com/attachments/796907538570412033/798242397070032926/GlitchBotsHomeIcon.png")
    botInfoEmbed.add_field(name="Version:", value=botVersion, inline=True)
    botInfoEmbed.add_field(name="Last Updated:", value=botUpdateDate, inline=True)
    botInfoEmbed.add_field(name="Last Restart:", value=db["Last Restart"], inline=True)
    botInfoEmbed.set_footer(text=f"Bot ID: {self.client.user.id}")
    await ctx.send(embed=botInfoEmbed)

  # Command for displaying bot info
  @commands.command()
  async def serverInfo(self, ctx):
    # Find the number of members not inlcuding the number of bots
    memberCount = ctx.guild.member_count
    botCount = 0

    for member in ctx.guild.members:
      if member.bot:
        memberCount -= 1
        botCount += 1

    # Create and send the server info embed
    serverInfoEmbed = discord.Embed(title= ctx.guild.name + " Info:", color=colors["GGpurple"])
    serverInfoEmbed.set_thumbnail(url=ctx.guild.icon_url)
    serverInfoEmbed.add_field(name="Owner:", value=ctx.guild.owner.name, inline=True)
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
    if user.name != "BetaBot":
      # Create a user info embed
      if str(user.color) != "#000000":
        userInfoEmbed = discord.Embed(title=user.name, color=user.color)
      else:
        userInfoEmbed = discord.Embed(title=user.name, color=colors["GGpurple"])
      
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
    # Get the correct information using the dev server IDs
    devServer = self.client.get_guild(guilds["GlitchBot's Home"])
    devChannel = devServer.get_channel(channels["gbhBugReports"])
    devRole = devServer.get_role(roles["gbhDevelopers"])

    # Create a bug report embed and send it
    bugReportEmbed = discord.Embed(title=f"Bug report from {ctx.guild.name}:", description=bugDesc, color=colors["GGred"])
    bugReportEmbed.set_author(name=f"{ctx.message.author.name} has found a bug", icon_url=ctx.message.author.avatar_url)
    bugReportEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804187951529197628/bugreport.png")
    bugReportEmbed.set_footer(text=f"Report made on {(datetime.datetime.now()).strftime('%x at %X')}")

    await devChannel.send(content=f"{devRole.mention}", embed=bugReportEmbed)
    await ctx.send("**The developers have received your report.** Thanks for submitting the issue!")

  # Suggestion command
  @commands.command()
  async def suggest(self, ctx, *, suggestion: str):
    # Get the correct information using the dev server IDs
    devServer = self.client.get_guild(guilds["GlitchBot's Home"])
    devChannel = devServer.get_channel(channels["gbhSuggestions"])
    devRole = devServer.get_role(roles["gbhDevelopers"])

    # Create a suggestion embed and send it
    suggestionEmbed = discord.Embed(title=f"Suggestion from {ctx.guild.name}:", description=suggestion, color=colors["GGblue"])
    suggestionEmbed.set_author(name=f"{ctx.message.author.name} has a suggestion", icon_url=ctx.message.author.avatar_url)
    suggestionEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/809597548523552788/suggestion.png")

    await devChannel.send(content=f"{devRole.mention}", embed=suggestionEmbed)
    await ctx.send("**The developers have received your suggestion.** Thanks for submitting your idea!")

def setup(client):
  client.add_cog(General(client))