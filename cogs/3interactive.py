import discord
from discord.ext import commands
from replit import db
import json

# Store necessary info locally from the JSON file
with open('globalVars.json', 'r') as jsonFile:
  globalVars = json.load(jsonFile)

colors = {}
for color in globalVars["embedColors"]:
  colors[color["color"]] = int(color["hex"], 0)

# Function for removing punctuation from parts of db keys
def clearPunctuation(string):
  punctuation = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
  for character in string:
    if character in punctuation:
      string = string.replace(character, "")
  
  return string

# Denotes this code as a class of commands under the name Interactive and initializes it
class Interactive(commands.Cog):
  def __init__(self, client):
    self.client = client
    
    # Gives this cog the attributes needed for the auto help command.
    self.parameters = ["<name> <desc> <:emoji1:> <option1> (...)", "<pollName>", 
    "<pollName>", "<name> <desc> <type> <persist> <:emoji1:> <@role1> (...)",
    "<messageID> <name> <type> <persist> <:emoji1:> <@role1> (...)", "<pollName>",
    "<pollName>"]

    self.shortDescs = ["Creates a poll.", "Displays the specified poll's results.",
    "Deletes the specified poll.", "Creates a role menu.",
    "Converts the specified role menu to a GlitchBot-compatible one.",
    "Removes the specified menu as a role menu.",
    "Deletes the specified menu."]

    self.longDescs = [
      "Creates a poll embed with poll info and a selection key.",
      "Tallys up the specified poll's reactions and displays the results (as of closure) in an embed.",
      "Deletes the specified poll without displaying results or notifying anyone.",
      "Creates a role menu embed with role info and a selection key.",
      "Converts an already-created role menu from either a bot or user into one which can be used with GlitchBot. Useful if you want to get rid of other bots without requiring users to re-select their roles in a new menu.",
      "Removes role menu functionality from the specified role menu. The role menu message will not be deleted, but it will no longer function as a role menu. If persist is on,roles granted from the menu will remain. If persist is off, all menus granted from the menu will be removed.",
      "Deletes the specified role menu preventing further role selection."
    ]

    self.paramDescs = [
      "`<name>` The name of the poll or question being asked.\n`<desc>` A brief description of what the poll's about or for.\n`<:emoji1:>` The emoji to be used for the following <option>.\n`<option1>` The option that goes with the previous <:emoji:>.\n`(...)` To add more options, simply add more pairs of emojis and options.\n__You must declare at least two options to create a poll.__",
      "`<pollName>` The exact name of the poll you wish to close.",
      "`<pollName>` The exact name of the poll you wish to delete.",
      "`<name>` The name of the role menu.\n`<desc>` A brief description of what the role menu is for.\n`<type>` The type of role menu you wish to create, either 'single' or 'multi'. Single allows selection of only one role at a time whereas multi allows members to select however many roles they'd like.\n`<persist>` Either 'yes' or 'no'. If yes, the user's last-selected role will stay applied even if no roles are selected in the menu. If the menu is ever deleted, each user's roles will stay applied too. If no, the user will not have any roles if none are selected in the menu. If the menu is ever deleted, each user's roles will be deleted as well.\n`<:emoji1:>` The emoji that corresponds to the following <@role>.\n`<@role1>` The role mention that goes with the previous <:emoji:>.\n`(...)` To add more roles, simply add more pairs of emojis and role pings.",
      "`<messageID>` The message ID of the role menu you are trying to convert.\n`<name>` The name you'd like to give the specified role menu.\n`<type>` The type of role menu you are trying to convert, either 'single' or 'multi'. Single allows selection of only one role at a time whereas multi allows members to select however many roles they'd like.\n`<persist>` Either 'yes' or 'no'. If yes, the user's last-selected role will stay applied even if no roles are selected in the menu. If the menu is ever deleted, each user's roles will stay applied too. If no, the user will not have any roles if none are selected in the menu. If the menu is ever deleted, each user's roles will be deleted as well.\n`<:emoji1:>` The emoji in the original menu that corresponds to the following <@role>.\n`<@role1>` The role mention that goes with the previous <:emoji:>.\n`(...)` To register more roles, simply add more pairs of emojis and role pings.",
      "`<pollName>` The exact name of the role menu whose functionality you wish to remove.",
      "`<pollName>` The exact name of the role menu you wish to delete."
    ]

    self.restrictions = ["Anyone", "Only the poller", "Only the poller or a member of power", "Only admins and owners", "Only admins and owners",
    "Only the menu creator and owners", "Only the menu creator and owners"]
  
  # Check for admin level or above
  def isAdminOrAbove(ctx):
    return (ctx.message.author.top_role.name == "Admins") or (ctx.message.author.top_role.name == "Owners")

  # On role menu reaction add event
  @commands.Cog.listener()
  async def on_raw_reaction_add(self, payload):
    if not payload.member.bot:
      # Check if the reaction is on a role menu message and only proceed if so
      isMenuReaction = False
      for key in db.prefix("ID For Menu"):
        if payload.message_id == db[key]:
          isMenuReaction = True
          menuName = key[12:]
    
      if payload.emoji is discord.Emoji:
        emoji = self.client.get_emoji(payload.emoji.id)
      else:
        emoji = str(payload.emoji)

      if isMenuReaction and (emoji in db["Emojis For Menu " + menuName]):
        # Fetch the necessary info for changing the user's roles
        guild = self.client.get_guild(payload.guild_id)
        user = payload.member
        index = (db["Emojis For Menu " + menuName]).index(emoji)
        addRole = guild.get_role(db["Role IDs For Menu " + menuName][index])

        # Follow the correct course-of-action based on the role menu type
        if db["Type For Menu " + menuName] == "single":
          for otherRoleID in db["Role IDs For Menu " + menuName]:
            otherRole = guild.get_role(otherRoleID)
            if otherRole in user.roles:
              await user.remove_roles(otherRole)
        
        await user.add_roles(addRole)
  
  # On role menu reaction remove event
  @commands.Cog.listener()
  async def on_raw_reaction_remove(self, payload):
    if True:
      # Check if the reaction is on a role menu message and only proceed if so
      isMenuReaction = False
      for key in db.prefix("ID For Menu"):
        if payload.message_id == db[key]:
          isMenuReaction = True
          menuName = key[12:]
    
      if payload.emoji is discord.Emoji:
        emoji = self.client.get_emoji(payload.emoji.id)
      else:
        emoji = str(payload.emoji)

      if (isMenuReaction and (emoji in db["Emojis For Menu " + menuName])) and (db["Persist For Menu " + menuName] == "no"):
        # Fetch the necessary info for changing the user's roles
        guild = self.client.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        index = (db["Emojis For Menu " + menuName]).index(emoji)
        removeRole = guild.get_role(db["Role IDs For Menu " + menuName][index])

        # Follow the correct course-of-action based on whether the role should persist
        otherRolesSelected = False
        channel = guild.get_channel(payload.channel_id)
        roleMenu = await channel.fetch_message(payload.message_id)
        for reaction in roleMenu.reactions:
          reactionUsers = await reaction.users().flatten()
          if (reaction.emoji in db["Emojis For Menu " + menuName]) and (user in reactionUsers):
            otherRolesSelected = True
          
        if not otherRolesSelected:
          for roleID in db["Role IDs For Menu " + menuName]:
            await user.remove_roles(guild.get_role(roleID))
        else:
          await user.remove_roles(removeRole)

  # Poll creation command
  @commands.command()
  async def poll(self, ctx, *, args:str):
    # Start by parsing the options to ensure the command can actually be executed
    start = 0
    end = 0
    i = 1

    # Obtain the poll's metadata by parsing the first two substrings
    name = None
    desc = None
    while i <= 2:
      start = args.find('"', start) + 1
      end = args.find('"', start)
      if i == 1:
        name = clearPunctuation(args[start:end])
      else:
        desc = args[start:end]
      start = end + 1
      i += 1

    # Create an emoji and option list by parsing the remaining portion of the string
    optionsStart = start
    options = []
    numOfOptions = 0
    while args.find('"', start) != -1:
      start = args.find('"', start) + 1
      end = args.find('"', start)
      options.append(args[start:end])
      start = end + 1
      numOfOptions += 1

    start = optionsStart
    emojis = []
    start += 1
    i = 0
    while i <= numOfOptions:
      end = args.find('"', start) - 1
      if args[start:end] != "":
        emojis.append(args[start:end])
      start = args.find('"', end)
      start = args.find('"', start + 1) + 2
      i += 1

    # If there is at least 2 options each with their own emoji, proceed to send an embed.
    # Otherwise, determine the error and send the appropriate error message
    if (((len(options) + len(emojis)) % 2) == 0) and ((len(options) >= 2) and (len(emojis)  >= 2)):
      pollEmbed = discord.Embed(title=name, description=desc, color=colors["GGpurple"])
      pollEmbed.set_author(name=f"{ctx.message.author.display_name} started a poll",  icon_url=ctx.message.author.avatar_url)
      pollEmbed.set_thumbnail (url="https://cdn.discordapp.com/attachments/796907538570412033/814685438446141490/poll.png")

      keyString = ""
      i = 0
      for option in options:
        keyString = keyString + emojis[i] + " " + options[i] + "\n"
        i += 1

      pollEmbed.add_field(name="Options:", value= keyString, inline=False)

      poll = await ctx.send(embed=pollEmbed)

      for emoji in emojis:
        await poll.add_reaction(emoji)

      name = clearPunctuation(name)
      db["ID For Poll " + name] = poll.id
      db["Poller ID For Poll " + name] = ctx.message.author.id
      db["Options For Poll " + name] = options
      db["Emojis For Poll " + name] = emojis

    elif (len(options) < 2) and (len(emojis) < 2):
      await ctx.send("**Sorry, but you need at least 2 options to start a poll!** If you  included 2 options, ensure each is surrounded by quotation marks then try again.")
    elif ((len(options) + len(emojis)) % 2) != 0:
      await ctx.send("**Sorry, but it appears you've left out an emoji or option.** Please  check your formatting then try again.")
    else:
      await ctx.send("**Sorry, but I can't interpret your formatting.** Please ensure each option is surrounded by quotation marks, then try again.")

  # Close poll command
  @commands.command()
  async def closePoll(self, ctx, *, name: str):
    name = clearPunctuation(name)

    # Ensure the person deleting the event is its host
    if ((("ID For Poll " + name) in db) and (ctx.message.author.id == db["Poller ID For Poll " + name])) and (db["ID For Poll " + name] != None):
      # Retrieve the original poll data for processing
      poll = await ctx.channel.fetch_message(db["ID For Poll " + name])
      options = db["Options For Poll " + name]

      # Collect all the responses in a formatted string
      option = 0
      results = ""
      for reaction in poll.reactions:
        if reaction in db["Emojis For Poll " + name]:
          results = results + str(reaction.emoji) + " " + str(reaction.count - 1) + " | " + options[option] + "\n"
          option += 1
      
      results = results + "\n**Thank you to all who responded!**"

      await poll.delete()
      db["ID For Poll " + name] = None
      # Create the results embed and send it
      resultsEmbed = discord.Embed(title=f'The results for "{name}" are in!', description=f"Here's how others responded!\n\n**Results:**\n{results}", color=colors["GGpurple"])
      resultsEmbed.set_author(name=f"{ctx.message.author.display_name} closed a poll", icon_url=ctx.message.author.avatar_url)
      resultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/815423018289070090/pollresults.png")

      await ctx.send(embed=resultsEmbed)
    elif (("ID For Poll " + name) not in db) or db["ID For Poll " + name] == None:
      await ctx.send("**Sorry, but that poll has either been already closed or does not exist!**")
    elif ctx.message.author.id != db["Poller ID For Poll " + name]:
      poller = self.client.get_user(db["Poller ID For Poll " + name])
      await ctx.send(f"**Sorry, but only the poller can close the poll!** Please reach out to {poller.name} to do so.")

  # Delete poll command
  @commands.command()
  async def deletePoll(self, ctx, *, name: str):
    name = clearPunctuation(name)
    
    # Ensure the person deleting the poll is either the poller or a member of power
    pollerOrMod = False
    if ctx.message.author.id == db["Poller ID For Poll " + name]:
      pollerOrMod = True
    if (ctx.message.author.top_role.name == "Mods") or (ctx.message.author.top_role.name == "Admins" or ctx.message.author.top_role.name == "Owners"):
      pollerOrMod = True
    
    if ((("ID For Poll " + name) in db) and (db["ID For Poll " + name] != None)) and pollerOrMod:
      poll = await ctx.channel.fetch_message(db["ID For Poll " + name])
      await poll.delete()
      db["ID For Poll " + name] = None
      await ctx.send(f"**{name} poll was deleted.**")
    elif ("ID For Poll " + name) not in db:
      await ctx.send("**Sorry, but I can't find a poll with that name!** Check that the poll exists and you are spelling its name correctly.")
    elif db["ID For Poll " + name] == None:
      await ctx.send("**Sorry, but that poll has already been closed!**")
    elif not pollerOrMod:
      await ctx.send("**Sorry, but only the poller and members of power can delete poll!**")

  # Role menu creation command
  @commands.command()
  @commands.check(isAdminOrAbove)
  async def menu(self, ctx, *, args:str):
    # Start by parsing the options to ensure the command can actually be executed
    start = 0
    end = 0
    i = 1

    # Obtain the menu's metadata by parsing the first three substrings
    name = None
    desc = None
    menuType = None
    persist = None
    while i <= 4:
      start = args.find('"', start) + 1
      end = args.find('"', start)
      if i == 1:
        name = clearPunctuation(args[start:end])
      elif i == 2:
        desc = args[start:end]
      elif i == 3:
        menuType = (args[start:end]).lower()
      else:
        persist = (args[start:end]).lower()
      start = end + 1
      i += 1

    # Create an emoji and option list by parsing the remaining portion of the string
    rolesStart = start
    roles = []
    numOfRoles = 0

    while args.find('>', start) != -1:
      start = args.find('<', start) + 1
      end = args.find('>', start)
      role = ctx.guild.get_role(int(args[(start + 2):end])) # Add 1 to eac
      roles.append(role)
      start = end + 1
      numOfRoles += 1

    start = rolesStart
    emojis = []
    start += 1
    i = 0
    while i <= numOfRoles:
      end = args.find('<', start) - 1
      if args[start:end] != "":
        emojis.append(args[start:end])
      start = args.find('<', end)
      start = args.find('>', start + 1) + 2
      i += 1

    validTypes = ["single", "multi"]
    validPersists = ["yes", "no"]

    # If there is at least 2 options each with their own emoji, proceed to send an embed.
    # Otherwise, determine the error and send the appropriate error message
    if ((menuType in validTypes) and (persist in validPersists)) and (((len(roles) + len(emojis)) % 2) == 0):
      menuEmbed = discord.Embed(title=name, description=desc, color=colors["GGpurple"])
      menuEmbed.set_author(name=f"{ctx.message.author.display_name} created a role menu",  icon_url=ctx.message.author.avatar_url)
      menuEmbed.set_thumbnail (url="https://cdn.discordapp.com/attachments/796907538570412033/816827696855515176/rolemenu.png")

      # Create the menu warning based on the menu's settings and add it, along with the key, as a field
      menuWarning = None
      if menuType == "single":
        menuWarning = "This is a single-choice role menu, only one of the following roles can be active at a time. "
      else:
        menuWarning = "This is a multi-choice role menu. All roles you select will be applied. "
      
      if persist == "yes":
        menuWarning = menuWarning + "Perist is also on, so all roles will remain applied to you even if you unselect them."
      else:
        menuWarning = menuWarning + "Persist is also off, so deselecting any role will remove it from you."

      keyString = ""
      i = 0
      for role in roles:
        keyString = keyString + emojis[i] + " " + (roles[i]).name + "\n"
        i += 1

      menuEmbed.add_field(name="Options:", value=f"{menuWarning}\n\n{keyString}", inline=False)

      menu = await ctx.send(embed=menuEmbed)

      # Add the specified reactions and save the menu's data so it can be used in later 
      # calls
      for emoji in emojis:
        await menu.add_reaction(emoji)

      db["ID For Menu " + name] = menu.id
      db["Creator ID For Menu " + name] = ctx.message.author.id
      db["Emojis For Menu " + name] = emojis

      roleIDs = []
      for role in roles:
        roleIDs.append(role.id)

      db["Role IDs For Menu " + name] = roleIDs
      db["Type For Menu " + name] = menuType
      db["Persist For Menu " + name] = persist

    elif ((len(roles) + len(emojis)) % 2) != 0:
      await ctx.send("**Sorry, but it appears you've left out an emoji or option.** Please  check your formatting then try again.")
    elif menuType not in validTypes:
      await ctx.send("**Sorry, but you must include a valid role menu type.** Please specify either single or multi then try again.")
    elif persist not in validPersists:
      await ctx.send("**Sorry, but you must specify whether role selections should persist.** Please include either yes or no then try again.")
    else:
      await ctx.send("**Sorry, but I can't interpret your formatting.** Please ensure each option is surrounded by quotation marks, then try again.")

  @commands.command()
  @commands.check(isAdminOrAbove)
  async def convertMenu(self, ctx, *, args: str):
    # Start by parsing the options to ensure the command can actually be executed
    start = 0
    end = 0
    i = 1

    # Obtain the menu's metadata by parsing the first three substrings
    menuID = None
    name = None
    menuType = None
    persist = None
    while i <= 4:
      start = args.find('"', start) + 1
      end = args.find('"', start)
      if i == 1:
        menuID = int(args[start:end])
      elif i == 2:
        name = clearPunctuation(args[start:end])
      elif i == 3:
        menuType = (args[start:end]).lower()
      else:
        persist = (args[start:end]).lower()
      start = end + 1
      i += 1

    # Create an emoji and option list by parsing the remaining portion of the string
    rolesStart = start
    roles = []
    numOfRoles = 0
    while args.find('>', start) != -1:
      start = args.find('<', start) + 1
      end = args.find('>', start)
      role = ctx.guild.get_role(int(args[(start + 2):end])) # Add 1 to eac
      roles.append(role)
      start = end + 1
      numOfRoles += 1

    start = rolesStart
    emojis = []
    start += 1
    i = 0
    while i <= numOfRoles:
      end = args.find('<', start) - 1
      if args[start:end] != "":
        emojis.append(args[start:end])
      start = args.find('<', end)
      start = args.find('>', start + 1) + 2
      i += 1

    validTypes = ["single", "multi"]
    validPersists = ["yes", "no"]

    numOfReactions = 0
    roleMenu = await ctx.channel.fetch_message(menuID)
    if roleMenu.reactions:
      for reaction in roleMenu.reactions:
        if reaction.emoji in emojis:
          numOfReactions += 1

    # If there is at least 2 options each with their own emoji, proceed to save the menu.
    # Otherwise, determine the error and send the appropriate error message
    if ((menuType in validTypes) and (persist in validPersists)) and ((((len(roles) + len(emojis)) % 2) == 0) and (numOfReactions == len(emojis))):
      # Save the role menu's information so it behaves like a standard GlitchBot menu
      db["ID For Menu " + name] = menuID
      db["Creator ID For Menu " + name] = ctx.message.author.id
      db["Emojis For Menu " + name] = emojis

      roleIDs = []
      for role in roles:
        roleIDs.append(role.id)

      db["Role IDs For Menu " + name] = roleIDs
      db["Type For Menu " + name] = menuType
      db["Persist For Menu " + name] = persist

      for emoji in emojis:
        await roleMenu.add_reaction(emoji)

      await ctx.send("**Role menu successfully converted!**")

    elif numOfReactions != len(emojis):
      await ctx.send("**Sorry, but it appears the role menu you are trying to convert is missing a reaction you specified.** Please check the original role menu then try again.") 
    elif ((len(roles) + len(emojis)) % 2) != 0:
      await ctx.send("**Sorry, but it appears an option is missing an emoji or an emoji is missing an option.** Please  check your formatting then try again.")
    elif menuType not in validTypes:
      await ctx.send("**Sorry, but you must include a valid role menu type.** Please specify either single or multi then try again.")
    elif persist not in validPersists:
      await ctx.send("**Sorry, but you must specify whether role selections should persist.** Please include either yes or no then try again.")
    else:
      await ctx.send("**Sorry, but I can't interpret your formatting.** Please ensure each option is surrounded by quotation marks, then try again.")
  
  # Role menu removal command
  @commands.command()
  @commands.check(isAdminOrAbove)
  async def removeMenu(self, ctx, *, name):
    name = clearPunctuation(name)

    # Check that the person attempting to remove the menu is the creator or an owner
    if ((("ID For Menu " + name) in db) and (db["ID For Menu " + name] != None)) and ((ctx.message.author.top_role.name == "Owners") or (ctx.message.author.id == db["Creator ID For Menu " + name])):
      roleMenu = await ctx.channel.fetch_message(db["ID For Menu " + name])

      # Remove all bot reactions from the message TODO figure out why tf it isn't working
      bot = await ctx.guild.fetch_member(800217314695577661)
      for emoji in db["Emojis For Menu " + name]:
        await roleMenu.remove_reaction(emoji, bot)

      # If persist is off, delete all the selected roles
      if db["Persist For Menu " + name] == "no":
        index = 0
        for reaction in roleMenu.reactions:
          reactionUsers = await reaction.users().flatten()
          for reactionUser in reactionUsers:
            if not reactionUser.bot:
              removeRole = ctx.guild.get_role(db["Role IDs For Menu " + name][index])
              await reactionUser.remove_roles(removeRole)
          index += 1
      db["ID For Menu " + name] = None
      await ctx.send(f"**{name} is no longer a role menu.**")
    elif ctx.message.author.id != db["Creator ID For Menu " + name]:
      await ctx.send("**Sorry, but you must be the menu's creator to remove it.**")
    elif ("ID For Menu " + name) not in db:
      await ctx.send("**Sorry, but I can't find a role menu with that name!** Check that the menu exists and you are spelling its name correctly.")
    elif db["ID For Menu " + name] == None:
      await ctx.send("**Sorry, but that role menu has already been removed or deleted!**")

  # Role menu deletion command
  @commands.command()
  @commands.check(isAdminOrAbove)
  async def deleteMenu(self, ctx, *, name):
    name = clearPunctuation(name)

    # Check that the person attempting to delete the menu is the creator or an owner
    if ((("ID For Menu " + name) in db) and (db["ID For Menu " + name] != None)) and ((ctx.message.author.top_role.name == "Owners") or (ctx.message.author.id == db["Creator ID For Menu " + name])):
      roleMenu = await ctx.channel.fetch_message(db["ID For Menu " + name])
      
      # If persist is off, delete all the selected roles
      if db["Persist For Menu " + name] == "no":
        index = 0
        for reaction in roleMenu.reactions:
          reactionUsers = await reaction.users().flatten()
          for reactionUser in reactionUsers:
            if not reactionUser.bot:
              removeRole = ctx.guild.get_role(db["Role IDs For Menu " + name][index])
              await reactionUser.remove_roles(removeRole)
          index += 1

      await roleMenu.delete()
      db["ID For Menu " + name] = None
      await ctx.send(f"**{name} role menu was deleted.**")
    elif ctx.message.author.id != db["Creator ID For Menu " + name]:
      await ctx.send("**Sorry, but you must be the menu's creator to delete it.**")
    elif ("ID For Menu " + name) not in db:
      await ctx.send("**Sorry, but I can't find a role menu with that name!** Check that the menu exists and you are spelling its name correctly.")
    elif db["ID For Menu " + name] == None:
      await ctx.send("**Sorry, but that role menu has already been removed or deleted!**")

def setup(client):
  client.add_cog(Interactive(client))