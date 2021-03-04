import discord
import os
import random
import string
import asyncio
import json
from datetime import date
from discord.ext import commands
from replit import db

# Declares this bot's intents
intents = discord.Intents(members=True, guilds=True, bans=True, invites=True, messages=True, reactions=True)

# Set the command prefix and additional bot settings
client = commands.Bot(command_prefix='!!', intents=intents, help_command=None, owner_id=os.environ['JustinID'])

# Updates every time the bot is restarted
db["Last Restart"] = (date.today()).strftime("%m/%d/%y")

# Reset the forceStop code
db["forceStop Confirmation Code"] = None

# Store necessary info locally from the JSON file
with open('globalVars.json', 'r') as jsonFile:
  globalVars = json.load(jsonFile)

colors = {}
for color in globalVars["embedColors"]:
  colors[color["color"]] = int(color["hex"], 0)

# FUNCTIONS ------------------------------------------------------------------

# Adds ordinals to the number passed and returns the two together
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

# Generates a random 6-character code
def randomCode(length):
  # List of characters [a-zA-Z0-9]
  chars = string.ascii_letters + string.digits
  code = ''.join(random.choice(chars) for _ in range(length))
  return code

def isDev(ctx):
  devs = [335440648393981952, 485182871867359255, 326453148178710530]
  return ctx.message.author.id in devs

# Create lists for groups (cogs), parameters, and descriptions so the commands here can be
# catalogued by the help command
groups = ["Developer", "Developer", "Developer", "Developer", "Developer",
"Developer", "General"]

names = ["forceStop", "clearDB", "unloadCog", "loadCog", "unloadCogs",
"loadCogs", "help"]

parameters = ["(code)", "(code)", "<cogName>", "<cogName>", "", "", "(commandName)"]

shortDescs = ["Force stops the bot.", "Clears the database.", "Unloads the specified cog.",
"Loads the specified cog.", "Unloads all cogs.", "Loads all cogs.",
"Displays command info."]

longDescs = [
  "Upon initiation, provides a random 6-digit code that must be entered alongside the command again to force stop, or power off, the bot. After successful confirmation, the bot will shut down within 5 minutes.",
  "Upon initiation, provides a random 6-digit code that must be entered alongside the command again to clear the bot's database. A database clear will cause the bot to forget everything in its memory, so all memory-requiring commands will not function when they try to retrieve previously stored information (like event deletion for prior events). A clear is useful, however, as it can eliminate unused keys and free up some database space. It may also help eliminate any ongoing actions that are stuck.",
  "Unloads the specified cog (or group of commands).",
  "Loads the specified cog (or group of commands).",
  "Unloads all currently loaded cogs (or groups of commands).",
  "Loads all currently unloaded cogs (or groups of commands).",
  "If a certain command is not specified, a list of active commands along with their parameters and brief descriptions is displayed. If a certain command is specified, displays a more detailed explanation of its use, parameters, and restrictions."]

paramDescs = [
  "`(code)` The 6-digit code only required to confirm a force stop. Included in the initiation message.",
  "`(code)` The 6-digit code only required to confirm a database clear. Included in the initiation message.",
  "`(cogName)` The exact name of a cog (or category name).",
  "`(cogName)` The exact name of a cog (or category name).",
  "", "", "`(commandName)` The exact name of a command (excluding prefix) only required for command-specific help."]

restrictions = ["Only developers", "Only developers", "Only developers", "Only developers", "Only developers",
"Only developers", "Anyone"]

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
    await client.change_presence(status=discord.Status.online, activity=discord.Game("The Development Game"))

# EVENTS ------------------------------------------------------------------

# Sends an embed to the announcements channel on member join
@client.event
async def on_member_join(member):
  channel = member.guild.system_channel
  joinEmbed = discord.Embed(title=f"Welcome to {member.guild.name}, {member.name}!", color=colors["GGblue"])
  joinEmbed.set_author(name=f"{member.name} joined the server | {ordinal(len(member.guild.members))} member", icon_url=member.avatar_url)
  joinEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/798607925882126346/memberjoin.png")
  await channel.send(embed=joinEmbed)
  db["Warnings For " + str(member.id)] = 0

# Sends an embed to the announcements channel on member leave (self-leave or kick, not ban)
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

# Sends an embed to the announcements channel on member ban
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
@commands.check(isDev)
async def forceStop(ctx, inputCode:str= None):
  # If a force stop is not already in progress, reset force stop info and initiate the process
  if inputCode == None and (("forceStop Confirmation Code" not in db) or (db["forceStop Confirmation Code"] == None)):
    # Reset database info regarding the force stop process
    db["forceStop Confirmed"] = False
    db["forceStop Confirmation Code"] = randomCode(6)
    db["forceStop Confirmation Message ID"] = None

    # Log the initiation and message the channel with confirmation instructions
    print("Force stop initiated by " + ctx.message.author.display_name + ". Code: " + db["forceStop Confirmation Code"])
    confirmation = await ctx.send(f"**You are about to force stop BetaBot**. Send the command again with the code...\n`{db['forceStop Confirmation Code']}`\n...to confirm. The code expires in **10** seconds.")
    db["forceStop Confirmation Message ID"] = confirmation.id

    # Begin the countdown
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

  # Alert the user the user that a force stop is already in progress upon a re-initiation
  # attempt
  elif inputCode == None and db["forceStop Confirmation Code"] != None:
    await ctx.send(f"**Confirmation in progress!** Please enter the code `{db['forceStop Confirmation Code']}` to confirm!")

  # If the user enters the correct confirmation code, prevent the bot from receiving the
  # uptime ping and send/log a success message
  elif inputCode == db["forceStop Confirmation Code"] and db["forceStop Confirmation Code"] != None:
    db["forceStop Confirmed"] = True
    confirmation = await ctx.fetch_message(db["forceStop Confirmation Message ID"])
    print(f"Force stop confirmed by {ctx.message.author.display_name}!")
    await confirmation.edit(content="**Bot force stop confirmed.** The code is no longer usable.")
    confirmationEmbed = discord.Embed(title="Bot will shut down within 5 minutes...", color=colors["GGred"])
    confirmationEmbed.set_author(name=f"Force stop confirmed by {ctx.message.author.display_name}.", icon_url=ctx.message.author.avatar_url)
    confirmationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/800209126550011904/forcestop.png")
    
    await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game("Shutting down..."))
    await ctx.send(embed=confirmationEmbed)
    await ctx.send("**BetaBot cannot be force stopped as it does not run on the same system as GlitchBot!** However, the development session will time out after 5 minutes of inactivity anyway.")

# Command for clearing the bot's database
@client.command()
@commands.check(isDev)
async def clearDB(ctx, inputCode:str= None):
  # If a database clear is not already in progress, reset db clear info and initiate
  # the process
  if inputCode == None and (("clearDB Confirmation Code" not in db) or (db["clearDB Confirmation Code"] == None)):
    # Reset database info regarding the force stop process
    db["clearDB Confirmed"] = False
    db["clearDB Confirmation Code"] = randomCode(6)
    db["clearDB Confirmation Message ID"] = None

    # Log the initiation and message the channel with confirmation instructions
    print("Database clear initiated by " + ctx.message.author.display_name + ". Code: " + db["clearDB Confirmation Code"])
    confirmation = await ctx.send(f"**You are about to clear the BetaBot database**. Send the command again with the code...\n`{db['clearDB Confirmation Code']}`\n...to confirm. The code expires in **10** seconds.")
    db["clearDB Confirmation Message ID"] = confirmation.id

    # Begin the countdown
    countdown = 10

    # Update the countdown message as time runs out
    while countdown >= 1:
      await asyncio.sleep(1)
      countdown -= 1
      if not db["clearDB Confirmed"]:
        await confirmation.edit(content=f"**You are about to clear the BetaBot database**. Send the command again with the code...\n`{db['clearDB Confirmation Code']}`\n...to confirm. The code expires in **{str(countdown)}** seconds.")
    
    # If the database clear wasn't confirmed by the end of the countdown, update
    # the message
    if not db["clearDB Confirmed"]:
      db["clearDB Confirmation Code"] = None
      print("Database clear cancelled.")
      await confirmation.edit(content="**The code has expired.** Re-enter the `;;clearDB` command to try again")

  # Alert the user the user that a database clear is already in progress upon
  # a re-initiation attempt
  elif inputCode == None and db["clearDB Confirmation Code"] != None:
    await ctx.send(f"**Confirmation in progress!** Please enter the code `{db['clearDB Confirmation Code']}` to confirm!")

  # If the user enters the correct confirmation code, clear the bot's database
  elif inputCode == db["clearDB Confirmation Code"] and db["clearDB Confirmation Code"] != None:
    db["clearDB Confirmed"] = True
    confirmation = await ctx.fetch_message(db["clearDB Confirmation Message ID"])
    print(f"Database clear confirmed by {ctx.message.author.display_name}!")
    await confirmation.edit(content="**Database clear confirmed.** The code is no longer usable.")
    confirmationEmbed = discord.Embed(title="The database will be cleared shortly...", color=colors["GGred"])
    confirmationEmbed.set_author(name=f"Database clear confirmed by {ctx.message.author.display_name}.", icon_url=ctx.message.author.avatar_url)
    confirmationEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/815426922052845578/dbclear.png")

    await ctx.send(embed=confirmationEmbed)
    
    # Delete all the keys from the database except the ones which are always problematic
    problemKeys = ["clearDB Confirmed", "ID For Poll How long can I make this poll before it breaks?", "Options for Poll How long can I make this poll before it breaks?", "Poller ID For Poll How long can I make this poll before it breaks?"]
    for key in db:
      if key not in problemKeys:
        del db[key]

# Commands for loading/unloading specific cogs
@client.command()
@commands.check(isDev)
async def unloadCog(ctx, cogName):
  # Check that the cog exists before attempting to unload it
  cogFile = None
  
  for filename in os.listdir('./cogs'):
    if cogName.lower() in filename:
      cogFile = filename[:-3]

  # If the specified cog exists, attempt to unload it. Otherwise, send an error message
  try:
    if cogFile:
      client.unload_extension(f'cogs.{cogFile}')
      print(f"{ctx.message.author.name} unloaded the {cogName.title()} cog.")
      await ctx.send(f"**Unloaded cog:** {cogName.title()}")
    else:
      await ctx.send("**The specified cog does not exist.**")
  except:
    if isinstance(unloadCog.error, commands.MissingRole):
      await ctx.send("**Sorry, but only developers are allowed to do that!**")
    else:
      await ctx.send("**The specified cog is already unloaded.**")

@client.command()
@commands.check(isDev)
async def loadCog(ctx, cogName):
  # Check that the cog exists before attempting to load it
  cogFile = None
  
  for filename in os.listdir('./cogs'):
    if cogName.lower() in filename:
      cogFile = filename[:-3]
  
  # If the specified cog exists, attempt to unload it. Otherwise, send an error message
  try:
    if cogFile:
      client.load_extension(f'cogs.{cogFile}')
      print(f"{ctx.message.author.name} loaded the {cogName.title()} cog.")
      await ctx.send(f"**Loaded cog:** {cogName.title()}")
    else:
      await ctx.send("**The specified cog does not exist.**")
  except:
    if isinstance(loadCog.error, commands.MissingRole):
      await ctx.send("**Sorry, but only developers are allowed to do that!**")
    else:
      await ctx.send("**The specified cog is already loaded.**")

# Commands for loading/unloading all cogs at once
@client.command()
@commands.check(isDev)
async def unloadCogs(ctx):
  try:
    # Unload all cogs which have not already been unloaded, then send a message specifying
    # what was done
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
  except:
    if isinstance(unloadCogs.error, commands.MissingRole):
      await ctx.send("**Sorry, but only developers are allowed to do that!**")

@client.command()
@commands.check(isDev)
async def loadCogs(ctx):
  try:
    # Load all cogs which have not already been loaded, then send a message specifying what was
    # done
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
  except:
      if isinstance(loadCogs.error, commands.MissingRole):
        await ctx.send("**Sorry, but only developers are allowed to do that!**")

# Smart help command that automatically catalogues loaded cogs and commands
@client.command()
async def help(ctx, inputCommand:str = None):
  if inputCommand == None:
    # Set up the base help embed
    helpEmbed = discord.Embed(title="Here's a list of commands:", description="Required   parameters in <>. Optional parameters in ().", color=colors["GGpurple"])

    # Here, cog refers to the groups of commands located outside this file. Group names
    # are for commands which belong in a cog, but are located in this file. All cogs are
    # groups, but not all groups are cogs in this case.

    # Ensure the help command is displayed regardless of whether or not the general cog
    # is loaded
    if "General" not in client.cogs:
      helpEmbed.add_field(name="General", value="`;;help (commandName)` Displays command info.", inline=False)

    # Iterate through all the loaded cogs
    for cogName in client.cogs:
      cog = client.get_cog(cogName)

      # If the cog has commands or there is a command within main.py that belongs to that
      # group, add those commands to the list
      if (len(cog.get_commands()) != 0) or cogName in groups:
        # This string variable will house all the commands and their information for every
        # group
        commandList = ""

        # If there is a command in main.py that belongs to the cog/group we're currently
        # registering, add it
        if cogName in groups:
          commandNum = 0
          # Scan through all the commands in main.py and add the ones that belong to the
          # cog/group we're currently registering
          for groupName in groups:
            # Format the command appropriately depending on whether it contains parameters
            if groupName == cogName:
              if parameters[commandNum] != "":
                commandList = commandList + "`!!" + names[commandNum] + " " + parameters  [commandNum] + "` " + shortDescs[commandNum] + "\n"
              else:
                commandList = commandList + "`!!" + names[commandNum] + "` " + shortDescs [commandNum] + "\n"
            commandNum += 1

        commandNum = 0
        # Add each cog's commands, parameters, and descriptions to the embed field
        for command in cog.get_commands():
          # Format the command appropriately depending on whether or not it contains parameters
          if cog.parameters[commandNum] != "":
            commandList = commandList + "`!!" + str(command) + " " + cog.parameters[commandNum]   + "` " + cog.shortDescs[commandNum] + "\n"
          else:
            commandList = commandList + "`!!" + str(command) + "` " + cog.shortDescs  [commandNum] + "\n"
          commandNum += 1

        # Finish this group of commands off by adding it to the help embed as a new field
        helpEmbed.add_field(name=cogName.title() + ":", value=commandList, inline=False)

    # Complete the embed by adding a thumbnail and WIP footer, then send it to the
    # requested channel
    helpEmbed.set_thumbnail (url="https://cdn.discordapp.com/attachments/796907538570412033/799741594701922354/help.png")
    helpEmbed.set_footer(text="This bot is currently a WIP. Commands are subject to change.")
    await ctx.send(embed=helpEmbed)
  else:
    inputCommand = inputCommand.lower()
    
    # Determine if the specified command exists and is loaded
    commandName = None
    commandNum = 0
    commandIndex = 0
    commandLocation = None
    for cogName in client.cogs:
      cog = client.get_cog(cogName)
      if (cogName in groups) and (commandName == None):
        for command in names:
          if inputCommand == command.lower():
            commandName = command
            commandLocation = "Main"
            commandIndex = commandNum
          commandNum += 1
      if commandName == None:
        commandNum = 0
        for command in cog.get_commands():
          if inputCommand == (str(command)).lower():
            commandName = command
            commandLocation = cog
            commandIndex = commandNum
          commandNum += 1
          
    # Send help information if the specified command is valid. Otherwise, send an error message
    if commandName != None:
      # Retrieve the specified command information and add it to an embed
      if commandLocation == "Main":
        if parameters[commandIndex] != "":
          helpEmbed = discord.Embed(title=f"!!{commandName} {parameters[commandIndex]}", color=colors["GGpurple"])
        else:
          helpEmbed = discord.Embed(title=f"!!{commandName}", color=colors["GGpurple"])
        
        helpEmbed.add_field(name="Description:", value=longDescs[commandIndex], inline=False)
        
        if parameters[commandIndex] != "":
          helpEmbed.add_field(name="Parameters:", value=paramDescs[commandIndex], inline=False)

        helpEmbed.add_field(name="Restrictions:", value=f"{restrictions[commandIndex]} can use this command.", inline=False)
      elif commandLocation != "Main":
        if commandLocation.parameters[commandIndex] != "":
          helpEmbed = discord.Embed(title=f"!!{commandName} {commandLocation.parameters[commandIndex]}", color=colors["GGpurple"])
        else:
          helpEmbed = discord.Embed(title=f"!!{commandName}", color=colors["GGpurple"])
        
        helpEmbed.add_field(name="Description:", value=commandLocation.longDescs[commandIndex], inline=False)

        if commandLocation.parameters[commandIndex] != "":
          helpEmbed.add_field(name="Parameters:", value=commandLocation.paramDescs[commandIndex], inline=False)
        
        helpEmbed.add_field(name="Restrictions:", value=f"{commandLocation.restrictions[commandIndex]} can use this command.", inline=False)

      helpEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/799741594701922354/help.png")
      helpEmbed.set_footer(text="This bot is currently a WIP. Commands are subject to change.")
      await ctx.send(embed=helpEmbed)
    else:
      await ctx.send("**Sorry, but the specified command is either disabled or does not exist.**")
      

# Start up the bot
client.run(os.getenv('Token'))