# Import the necessary libraries and modules for this code
import discord
import os
import random
import string
import asyncio
import json
from datetime import date
from discord.ext import commands
from replit import db

# Declares this bot's intents ("subscribes" to different events so the bot can "hear" them)
intents = discord.Intents(members=True, guilds=True, bans=True, invites=True, messages=True, reactions=True)

# Set the command prefix and additional bot settings. Use default intents.
client = commands.Bot(command_prefix='!!', intents=intents, help_command=None, owner_id=os.environ['JustinID'])

# Updates every time the bot is restarted. Used in the botInfo command
db["Last Restart"] = (date.today()).strftime("%m/%d/%y")

# Reset the forceStop code
db["forceStop Confirmation Code"] = None

# Store necessary info locally from JSON and env files
with open('globalVars.json', 'r') as jsonFile:
  globalVars = json.load(jsonFile)

# Store color codes
colors = {}
for color in globalVars["embedColors"]:
  colors[color["color"]] = int(color["hex"], 0)

# Custom functions
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

# Random char function
def randomCode(length):
    # List of characters [a-zA-Z0-9]
    chars = string.ascii_letters + string.digits
    code = ''.join(random.choice(chars) for _ in range(length))
    return code

# Create lists for group (cogs), parameters, and descriptions so the commands here can be
# catalogued by the help command
groups = ["Developer", "Developer", "Developer", "Developer",
"Developer", "General"]

names = ["forceStop","unloadCog", "loadCog", "unloadCogs",
"loadCogs", "help"]

parameters = ["(code)","<cogName>", "<cogName>", "", "", ""]

descriptions = ["Force stops the bot.", "Unloads the specified cog.",
"Loads the specified cog.", "Unloads all cogs.", "Loads all cogs.",
"Displays this message."]

# STARTUP ------------------------------------------------------------------

print("[STARTUP] Starting up...\n[STARTUP] Loading cogs...")

# Loads each cog within the cogs folder
for filename in os.listdir('./cogs'):
  if filename.endswith('.py'):
    client.load_extension(f'cogs.{filename[:-3]}')

print("[STARTUP] Cogs successfully loaded.\n[STARTUP] Resetting memory...")
# Reset forceStop confirmation memory
db["forceStop Confirmed"] = False
db["forceStop Confirmation Code"] = None
db["forceStop Confirmation Message ID"] = None
print("[STARTUP] Memory reset.")

# On startup console log and status setter
@client.event
async def on_ready():
    print('[STARTUP] Startup complete. BetaBot has logged in as {0.user}'.format(client))
    print('-------------------------------------')

    # Set bot status upon sucessful login
    await client.change_presence(status=discord.Status.online, 
    activity=discord.Game("The In-Development Game"))

# EVENTS ------------------------------------------------------------------

# Server join and leave events
# Embed for when a member joins
@client.event
async def on_member_join(member):
  # Determine the channel to send the join message to
  channel = member.guild.system_channel
  if str(member.guild) == "Glitched Gaming":
    joinEmbed = discord.Embed(title=f"Welcome to Glitched Gaming, {member.name}!", color=colors["GGblue"])
    joinEmbed.set_author(name=f"{member.name} joined the server | {ordinal(len(member.guild.members))} member", icon_url=member.avatar_url)
    joinEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/798607925882126346/memberjoin.png")
    await channel.send(embed=joinEmbed)
    db["Warnings For " + str(member.id)] = 0
  elif str(member.guild) == "GlitchBot's Home":
    joinEmbed = discord.Embed(title=f"Welcome to the GlitchBot development server, {member.name}!", color=colors["GGblue"])
    joinEmbed.set_author(name=f"{member.name} joined the server | {ordinal(len(member.guild.members))} member", icon_url=member.avatar_url)
    joinEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/798607925882126346/memberjoin.png")
    await channel.send(embed=joinEmbed)
    db["Warnings For " + str(member.id)] = 0
  else:
    joinEmbed = discord.Embed(title=f"Welcome to {str(member.guild)}, {member.name}!", color=colors["GGblue"])
    joinEmbed.set_author(name=f"{member.name} joined the server | {ordinal(len(member.guild.members))} member", icon_url=member.avatar_url)
    joinEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/798607925882126346/memberjoin.png")
    await channel.send(embed=joinEmbed)

# Embed for when a member leaves. Try/except ensures this isn't called for a ban.
@client.event
async def on_member_remove(member):
  try:
    await member.guild.fetch_ban(member)
  except:
    channel = member.guild.system_channel
    leaveEmbed = discord.Embed(title=f"Bye, {member.name}! See you around!", color=colors["GGred"])
    leaveEmbed.set_author(name=f"{member.name} left the server", icon_url=member.avatar_url)
    leaveEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/798608106057629766/memberleave.png")
    await channel.send(embed=leaveEmbed)

# Embed for when a member is banned
@client.event
async def on_member_ban(guild, member):
  channel = member.guild.system_channel
  banEmbed = discord.Embed(title=f"The almighty ban hammer has spoken. {member.name}, begone!", color=colors["GGred"])
  banEmbed.set_author(name=f"{member.name} was banned", icon_url=member.avatar_url)
  banEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/798752034077671464/memberban.png")
  await channel.send(embed=banEmbed)

# COMMANDS ------------------------------------------------------------------
# Command for force stopping the bot
@client.command()
@commands.has_role("Developers")
async def forceStop(ctx, inputCode=None):
  # If the command is being called the "first" time
  if inputCode == None and db["forceStop Confirmation Code"] == None:
    # Set the confirmation boolean to the default value of False
    db["forceStop Confirmed"] = False
    
    # Generate a random 6-character code and remember it
    db["forceStop Confirmation Code"] = randomCode(6)

    # Reset the bot's memory of the forceStop message ID
    db["forceStop Confirmation Message ID"] = None

    # Print to console and message the channel with confirmation info
    print("Force stop initiated by " + ctx.message.author.name + ". Code: " + db["forceStop Confirmation Code"])
    confirmation = await ctx.send(f"**You are about to force stop BetaBot**. Send the command again with the code...\n`{db['forceStop Confirmation Code']}`\n...to confirm. The code expires in **10** seconds.")
    db["forceStop Confirmation Message ID"] = confirmation.id

    # Start the countdown
    countdown = 10

    # Update the countdown message as time runs out
    while countdown >= 1:
      await asyncio.sleep(1)
      countdown -= 1
      if not db["forceStop Confirmed"]:
        await confirmation.edit(content=f"**You are about to force stop BetaBot**. Send the command again with the code...\n`{db['forceStop Confirmation Code']}`\n...to confirm. The code expires in **{str(countdown)}** seconds.")
    
    # If the force stop wasn't confirmed by the end of the countdown, update the message
    if not db["forceStop Confirmed"]:
      db["forceStop Confirmation Code"] = None
      print("Force stop cancelled.")
      await confirmation.edit(content="**The code has expired.** Re-enter the `;;forceStop` command to try again")

  # If the user attempts to start a new confirmation when one is already active
  elif inputCode == None and db["forceStop Confirmation Code"] != None:
    await ctx.send(f"**Confirmation in progress!** Please enter the code `{db['forceStop Confirmation Code']}` to confirm!")

  # If the user enters the correct confirmation code
  elif inputCode == db["forceStop Confirmation Code"] and db["forceStop Confirmation Code"] != None:
    db["forceStop Confirmed"] = True
    confirmation = await ctx.fetch_message(db["forceStop Confirmation Message ID"])
    print(f"Force stop confirmed by {ctx.message.author.name}! Preventing UpTime ping...")
    await confirmation.edit(content="**Bot force stop confirmed.** The code is no longer usable.")
    confirmationEmbed = discord.Embed(title="Bot will shut down within 5 minutes...", color=colors["GGred"])
    confirmationEmbed.set_author(name=f"Force stop confirmed by {ctx.message.author.name}.", icon_url=ctx.message.author.avatar_url)
    confirmationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/800209126550011904/forcestop.png")
    await ctx.send(embed=confirmationEmbed)
    await ctx.send("**BetaBot cannot be force stopped as it does not run on the same system as GlitchBot!** However, the development session will time out after 5 minutes of inactivity anyway.")

# Commands for loading/unloading specific cogs
@client.command()
@commands.has_role("Developers")
async def unloadCog(ctx, cogName):
  # If the user is a dev, load the specified cog. If an error occurs or the user is not a 
  # dev, determine the problem and respond with an appropriate error message.
  cogFile = None
  
  for filename in os.listdir('./cogs'):
    if cogName.lower() in filename:
      cogFile = filename[:-3]

  try:
    client.unload_extension(f'cogs.{cogFile}')
    print(f"{ctx.message.author.name} unloaded the {cogName.title()} cog.")
    await ctx.send(f"**Unloaded cog:** {cogName.title()}")
  except:
    if isinstance(unloadCog.error, commands.MissingRole):
      await ctx.send("**Sorry, but only developers are allowed to do that!**")
    elif ((cogFile + ".py") not in os.listdir('./cogs')):
      await ctx.send("**The specified cog does not exist.**")
    else:
      await ctx.send("**The specified cog is already unloaded.**")

@client.command()
@commands.has_role("Developers")
async def loadCog(ctx, cogName):
  # If the user is a dev, load the specified cog. If an error occurs or the user is not a
  # dev, determine the problem and respond with an appropriate error message.
  cogFile = None
  
  for filename in os.listdir('./cogs'):
    if cogName.lower() in filename:
      cogFile = filename[:-3]
  
  try:
    client.load_extension(f'cogs.{cogFile}')
    print(f"{ctx.message.author.name} loaded the {cogName.title()} cog.")
    await ctx.send(f"**Loaded cog:** {cogName.title()}")
  except:
    if isinstance(loadCog.error, commands.MissingRole):
      await ctx.send("**Sorry, but only developers are allowed to do that!**")
    elif ((cogFile + ".py") not in os.listdir('./cogs')):
      await ctx.send("**The specified cog does not exist.**")
    else:
      await ctx.send("**The specified cog is already loaded.**")

# Commands for loading/unloading all cogs at once
@client.command()
@commands.has_role("Developers")
async def unloadCogs(ctx):
  anythingUnloaded = False
  for filename in os.listdir('./cogs'):
    if (filename.endswith('.py') and (filename[:-3] != "developer")) and ((filename[:-3]   in str(client.cogs.values()))):
      client.unload_extension(f'cogs.{filename[:-3]}')
      anythingUnloaded = True
  
  if anythingUnloaded:
    print(f"{ctx.message.author.name} unloaded all cogs.")
    await ctx.send("**All cogs are now unloaded.**")
  else:
    await ctx.send("**All cogs are already unloaded.**")

@client.command()
@commands.has_role("Developers")
async def loadCogs(ctx):
  anythingLoaded = False
  for filename in os.listdir('./cogs'):
    if (filename.endswith('.py') and (filename[:-3] != "developer")) and ((filename[:-3]   not in str(client.cogs.values()))):
      client.load_extension(f'cogs.{filename[:-3]}')
      anythingLoaded = True
  
  if anythingLoaded:
    print(f"{ctx.message.author.name} loaded all cogs.")
    await ctx.send("**Successfully loaded all cogs.**")
  else:
    await ctx.send("**All cogs are already loaded.**")

# Smart help command which automatically adds/removes toggled cogs
@client.command()
async def help(ctx):
  # Set up the base help embed
  helpEmbed = discord.Embed(title="Here's a list of commands:", description="Required parameters in <>. Optional parameters in ().", color=colors["GGpurple"])

  # Here, cog refers to the groups of commands located outside this file. Group names
  # are for commands which belong in a cog, but are located in this file. All cogs are
  # groups, but not all groups are cogs in this case.
  
  # Ensure the help command is displayed regardless of whether or not the general cog
  # is loaded.
  if "General" not in client.cogs:
    helpEmbed.add_field(name="General", value="`;;help` Displays this message.", inline=False)
  
  # Iterate through all the loaded cogs
  for cogName in client.cogs:
    cog = client.get_cog(cogName)

    # If the cog has commands or there is a command within main.py that belongs to that
    # group, add those commands to the list.
    if (len(cog.get_commands()) != 0) or cogName in groups:
      # This string variable will house all the commands and their information for every
      # group
      commandList = ""
      
      # If there is a command in main.py that belongs to the cog/group we're currently
      # registering, add it.
      if cogName in groups:
        mainIterator = 0
        # Scan through all the commands in main.py and add the ones that belong to the
        # cog/group we're currently registering
        for groupName in groups:
          # Format the command appropriately depending on whether it contains parameters
          if groupName == cogName:
            if parameters[mainIterator] != "":
              commandList = commandList + "`!!" + names[mainIterator] + " " + parameters[mainIterator] + "` " + descriptions[mainIterator] + "\n"
            else:
              commandList = commandList + "`!!" + names[mainIterator] + "` " + descriptions[mainIterator] + "\n"
          mainIterator += 1

      commandNum = 0
      # Add each cog's commands, parameters, and descriptions to the embed field
      for command in cog.get_commands():
        # Format the command appropriately depending on whether it contains parameters
        if cog.parameters[commandNum] != "":
          commandList = commandList + "`!!" + str(command) + " " + cog.parameters[commandNum] + "` " + cog.descriptions[commandNum] + "\n"
        else:
          commandList = commandList + "`!!" + str(command) + "` " + cog.descriptions[commandNum] + "\n"
        commandNum += 1

      # Finish this group of commands off by adding it to the help embed as a new field
      helpEmbed.add_field(name=cogName.title() + ":", value=commandList, inline=False)

  # Complete the embed by adding a thumbnail and WIP footer, then send it to the
  # requested channel
  helpEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/799741594701922354/help.png")
  helpEmbed.set_footer(text="This bot is currently a WIP. Commands are subject to change.")
  await ctx.send(embed=helpEmbed)

# Bot startup
client.run(os.getenv('Token'))