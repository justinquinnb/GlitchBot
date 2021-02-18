import discord
from discord.ext import commands
from replit import db
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

# Denotes this code as a class of commands under the name General and initializes it
class General(commands.Cog):
  def __init__(self, client):
    self.client = client
    
    # Gives this cog the attributes needed for the auto help command.
    self.parameters = ["", "", "<@user>", "(vX.X.X)", "<desc>", "<desc>"]
    self.descriptions = ["Displays bot info.", "Displays server info.",
    "Displays user info.", "Displays update info.",
    "Report a bug to the GlitchBot devs.",
    "Suggest an idea to the GlitchBot devs."]

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

    botInfoEmbed = discord.Embed(title="BetaBot Info:", color=GGpurple)
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
    serverInfoEmbed = discord.Embed(title= ctx.guild.name + " Info:", color=GGpurple)
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
      # Create a user info embed:
      if str(user.color) != "#000000":
        userInfoEmbed = discord.Embed(title=user.name, color=user.color)
      else:
        userInfoEmbed = discord.Embed(title=user.name, color=GGpurple)
      
      userInfoEmbed.set_thumbnail(url=user.avatar_url)
      userInfoEmbed.add_field(name="Joined on:", value=user.joined_at.strftime("%m/%d/%y"), inline=True)
      userInfoEmbed.add_field(name="Registered on:", value=user.created_at.strftime("%m/%d/%y"), inline=True)

      powerRoles = ["Bots", "Owners", "Admins", "Mods", "Developers", "Testers"]

      if user.top_role.name not in powerRoles:
        userInfoEmbed.add_field(name="Server Role:", value="Member", inline=True)
      else:
        userInfoEmbed.add_field(name="Server Role:", value=user.top_role.name[:-1], inline=True)
      
      userInfoEmbed.set_footer(text=f"User ID: {user.id}")
        
      await ctx.send(embed=userInfoEmbed)
    else:
      await ctx.send("**You can't use the userInfo command on me!** Try the `;botInfo` command instead.")

  # Update info
  @commands.command()
  async def updateInfo(self, ctx, *, version: str=None):
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
    # Get the correct information using the dev server ids
    devServer = self.client.get_guild(789323920506486807)
    devChannel = devServer.get_channel(804169142876766230)
    devRole = devServer.get_role(796411321641467934)

    # Create a bug report embed
    bugReportEmbed = discord.Embed(title=f"Bug report from {ctx.guild.name}:", description=bugDesc, color=GGred)
    bugReportEmbed.set_author(name=f"{ctx.message.author.name} has found a bug", icon_url=ctx.message.author.avatar_url)
    bugReportEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/804187951529197628/bugreport.png")
    bugReportEmbed.set_footer(text=f"Report made on {(datetime.datetime.now()).strftime('%x at %X')}")

    await devChannel.send(content=f"{devRole.mention}", embed=bugReportEmbed)

  # Suggestion command
  @commands.command()
  async def suggest(self, ctx, *, suggestion: str):
    # Get the correct information using the dev server ids
    devServer = self.client.get_guild(789323920506486807)
    devChannel = devServer.get_channel(806004797232119838)
    devRole = devServer.get_role(796411321641467934)

    # Create a bug report embed
    suggestionEmbed = discord.Embed(title=f"Suggestion from {ctx.guild.name}:", description=suggestion, color=GGblue)
    suggestionEmbed.set_author(name=f"{ctx.message.author.name} has a suggestion", icon_url=ctx.message.author.avatar_url)
    suggestionEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/809597548523552788/suggestion.png")

    await devChannel.send(content=f"{devRole.mention}", embed=suggestionEmbed)

def setup(client):
  client.add_cog(General(client))