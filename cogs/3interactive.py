import discord
from discord.ext import commands
from replit import db
import string
from globalData import clearPunctuation, getConfig

# Denotes this code as a class of commands under the name Interactive and initializes it
class Interactive(commands.Cog):
  def __init__(self, client):
    self.client = client
  
  # Check for admin level or above
  def isAdminOrAbove(ctx):
    cfg = getConfig(ctx.guild.id)
    return (ctx.message.author.top_role.id == cfg["adminRole"]) or (ctx.message.author.id== ctx.guild.owner_id)

    # On role menu reaction add event
  @commands.Cog.listener()
  async def on_raw_reaction_add(self, payload):
    if not payload.member.bot:
      # Check if the reaction is on a role menu message and only proceed if so
      isMenuReaction = False
      keyPrefix = "ID For Menu " + str(payload.guild_id)
      menuName = ""
      
      for key in db.prefix(keyPrefix):
        if payload.message_id == db[key]:
          isMenuReaction = True
          menuName = key[(14 + len(payload.guild_id)):]
    
      if payload.emoji is discord.Emoji:
        emoji = self.client.get_emoji(payload.emoji.id)
      else:
        emoji = str(payload.emoji)

      keySuffix = str(payload.guild_id) + "-" + menuName
      if isMenuReaction and (emoji in db["Emojis For Menu " + keySuffix]):
        # Fetch the necessary info for changing the user's roles
        guild = self.client.get_guild(payload.guild_id)
        user = payload.member
        index = (db["Emojis For Menu " + keySuffix]).index(emoji)
        addRole = guild.get_role(db["Role IDs For Menu " + keySuffix][index])

        # Follow the correct course-of-action based on the role menu type
        if db["Type For Menu " + keySuffix] == "single":
          for otherRoleID in db["Role IDs For Menu " + keySuffix]:
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
      keyPrefix = "ID For Menu" + str(payload.guild_id)
      menuName = ""
      
      for key in db.prefix(keyPrefix):
        if payload.message_id == db[key]:
          isMenuReaction = True
          menuName = key[(14 + len(payload.guild_id)):]
    
      if payload.emoji is discord.Emoji:
        emoji = self.client.get_emoji(payload.emoji.id)
      else:
        emoji = str(payload.emoji)

      keySuffix = str(payload.guild_id) + "-" + menuName
      if (isMenuReaction and (emoji in db["Emojis For Menu " + keySuffix])) and (db["Persist For Menu " + keySuffix] == "no"):
        # Fetch the necessary info for changing the user's roles
        guild = self.client.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        index = (db["Emojis For Menu " + keySuffix]).index(emoji)
        removeRole = guild.get_role(db["Role IDs For Menu " + keySuffix][index])

        # Follow the correct course-of-action based on whether the role should persist
        otherRolesSelected = False
        channel = guild.get_channel(payload.channel_id)
        roleMenu = await channel.fetch_message(payload.message_id)
        for reaction in roleMenu.reactions:
          reactionUsers = await reaction.users().flatten()
          if (str(reaction.emoji) in db["Emojis For Menu " + keySuffix]) and (user in reactionUsers):
            otherRolesSelected = True
          
        if not otherRolesSelected:
          for roleID in db["Role IDs For Menu " + keySuffix]:
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

    numOfEmojis = len(emojis)
    numOfOptions= len(options)
    cfg = getConfig(ctx.guild.id)
    keySuffix = str(ctx.guild.id) + "-" + name

    # If there is at least 2 options each with their own emoji, proceed to send an embed.
    # Otherwise, determine the error and send the appropriate error message
    if (("ID For Poll " + keySuffix) not in db) and (((numOfOptions + numOfEmojis) % 2) == 0) and (((numOfEmojis >= 2) and (numOfOptions >= 2)) and ((numOfEmojis <= 20) and (numOfOptions <= 20))):
      pollEmbed = discord.Embed(title=name, description=desc, color=cfg["generalColor"])
      pollEmbed.set_author(name=f"{ctx.message.author.display_name} started a poll",  icon_url=ctx.message.author.avatar_url)
      pollEmbed.set_thumbnail (url="https://cdn.discordapp.com/attachments/796907538570412033/814685438446141490/poll.png")

      pollKeyString = ""
      i = 0
      for option in options:
        pollKeyString = pollKeyString + emojis[i] + " " + options[i] + "\n"
        i += 1

      pollEmbed.add_field(name="Options:", value= pollKeyString, inline=False)

      poll = await ctx.send(embed=pollEmbed)

      for emoji in emojis:
        await poll.add_reaction(emoji)

      name = clearPunctuation(name)

      db["ID For Poll " + keySuffix] = poll.id
      db["Poller ID For Poll " + keySuffix] = ctx.message.author.id
      db["Options For Poll " + keySuffix] = options
      db["Emojis For Poll " + keySuffix] = emojis

    elif ("ID For Poll " + keySuffix) in db:
      await ctx.send("**Sorry, but a poll with that name is already open!** Try a new name or delete/close the old poll then try again.")
    elif (numOfEmojis < 2) and (numOfOptions < 2):
      await ctx.send("**Sorry, but you need at least 2 options to start a poll!** If you  included 2 options, ensure each is surrounded by quotation marks then try again.")
    elif (numOfEmojis > 2) and (numOfOptions > 2):
      await ctx.send("**Sorry, but you can only have a max of 20 options per poll!** If you included less, ensure they are properly surrounded by quotation marks then try again.")
    elif ((numOfEmojis + numOfOptions) % 2) != 0:
      await ctx.send("**Sorry, but it appears you've left out an emoji or option.** Please  check your formatting then try again.")
    else:
      await ctx.send("**Sorry, but I can't interpret your formatting.** Please ensure each option is surrounded by quotation marks, then try again.")

  # Close poll command
  @commands.command()
  async def closePoll(self, ctx, *, name: str):
    name = clearPunctuation(name)
    keySuffix = str(ctx.guild.id) + "-" + name

    # Ensure the person deleting the event is its host
    if ((("ID For Poll " + keySuffix) in db) and (ctx.message.author.id == db["Poller ID For Poll " + keySuffix])) and (db["ID For Poll " + keySuffix] != None):
      # Retrieve the original poll data for processing
      poll = await ctx.channel.fetch_message(db["ID For Poll " + keySuffix])
      options = db["Options For Poll " + keySuffix]

      # Collect all the responses in a formatted string
      option = 0
      results = ""
      for reaction in poll.reactions:
        if reaction in db["Emojis For Poll " + keySuffix]:
          results = results + str(reaction.emoji) + " " + str(reaction.count - 1) + " | " + options[option] + "\n"
          option += 1
      
      results = results + "\n**Thank you to all who responded!**"
      cfg = getConfig(ctx.guild.id)

      await poll.delete()
      
      # Clear poll data from the database
      del db["ID For Poll " + keySuffix]
      del db["Poller ID For Poll " + keySuffix]
      del db["Options For Poll " + keySuffix]
      del db["Emojis For Poll " + keySuffix]

      # Create the results embed and send it
      resultsEmbed = discord.Embed(title=f'The results for "{name}" are in!', description=f"Here's how others responded!\n\n**Results:**\n{results}", color=cfg["generalColor"])
      resultsEmbed.set_author(name=f"{ctx.message.author.display_name} closed a poll", icon_url=ctx.message.author.avatar_url)
      resultsEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/796907538570412033/815423018289070090/pollresults.png")

      await ctx.send(embed=resultsEmbed)
    elif (("ID For Poll " + keySuffix) not in db) or db["ID For Poll " + keySuffix] == None:
      await ctx.send("**Sorry, but that poll has either been already closed or does not exist!**")
    elif ctx.message.author.id != db["Poller ID For Poll " + keySuffix]:
      poller = self.client.get_user(db["Poller ID For Poll " + keySuffix])
      await ctx.send(f"**Sorry, but only the poller can close the poll!** Please reach out to {poller.name} to do so.")

  # Delete poll command
  @commands.command()
  async def deletePoll(self, ctx, *, name: str):
    name = clearPunctuation(name)
    keySuffix = str(ctx.guild.id) + "-" + name
    
    # Ensure the person deleting the poll is either the poller or a member of power
    pollerOrMod = False
    if ctx.message.author.id == db["Poller ID For Poll " + keySuffix]:
      pollerOrMod = True

    cfg = getConfig(ctx.guild.id)

    if (ctx.message.author.top_role.id == cfg["modRole"]) or (ctx.message.author.top_role.id == cfg["adminRole"] or ctx.message.author.id == ctx.guild.owner_id):
      pollerOrMod = True
    
    if ((("ID For Poll " + keySuffix) in db) and (db["ID For Poll " + keySuffix] != None)) and pollerOrMod:
      poll = await ctx.channel.fetch_message(db["ID For Poll " + keySuffix])
      await poll.delete()

      # Clear poll data from the database
      del db["ID For Poll " + keySuffix]
      del db["Poller ID For Poll " + keySuffix]
      del db["Options For Poll " + keySuffix]
      del db["Emojis For Poll " + keySuffix]

      await ctx.send(f"**{name} poll was deleted.**")
    elif ("ID For Poll " + keySuffix) not in db:
      await ctx.send("**Sorry, but I can't find a poll with that name!** Check that the poll exists and you are spelling its name correctly.")
    elif db["ID For Poll " + keySuffix] == None:
      await ctx.send("**Sorry, but that poll has already been closed!**")
    elif not pollerOrMod:
      await ctx.send("**Sorry, but only the poller and members of power can delete poll!**")

  # Role menu creation command
  @commands.command()
  @commands.guild_only()
  @commands.check(isAdminOrAbove)
  async def roleMenu(self, ctx, *, args:str):
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

    while args.find('"', start) != -1:
      start = args.find('"', start) + 1
      end = args.find('"', start)
      role = ctx.guild.get_role(int(args[(start + 3):(end - 1)]))
      roles.append(role)
      numOfRoles += 1
      start = end + 1

    start = rolesStart
    emojis = []
    start += 1
    i = 0
    while i <= numOfRoles:
      end = args.find('"', start) - 1
      if args[start:end] != "":
        emojis.append(args[start:end])
      start = args.find('"', end)
      start = args.find('"', start + 1) + 2
      i += 1

    validTypes = ["single", "multi"]
    validPersists = ["yes", "no"]

    numOfRoles = len(roles)
    numOfEmojis = len(emojis)
    keySuffix = str(ctx.guild.id) + "-" + name

    # If there is at least 2 options each with their own emoji, proceed to send an embed.
    # Otherwise, determine the error and send the appropriate error message
    if (("ID For Menu " + keySuffix) not in db) and (((menuType in validTypes) and (persist in validPersists)) and ((((numOfRoles + numOfEmojis)) % 2) == 0)) and ((numOfRoles <= 20) and (numOfEmojis <= 20)):
      cfg = getConfig(ctx.guild.id)
      
      menuEmbed = discord.Embed(title=name, description=desc, color=cfg["generalColor"])
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

      db["ID For Menu " + keySuffix] = menu.id
      db["Creator ID For Menu " + keySuffix] = ctx.message.author.id
      db["Emojis For Menu " + keySuffix] = emojis

      roleIDs = []
      for role in roles:
        roleIDs.append(role.id)

      db["Role IDs For Menu " + keySuffix] = roleIDs
      db["Type For Menu " + keySuffix] = menuType
      db["Persist For Menu " + keySuffix] = persist

    elif ("ID For Menu " + keySuffix) in db:
      await ctx.send("**Sorry, but a menu with that name already exists!** Try a new name or delete/strip the original menu (deleteMenu <name>) then try again.")
    elif ((len(roles) + len(emojis)) % 2) != 0:
      await ctx.send("**Sorry, but it appears you've left out an emoji or option.** Please  check your formatting then try again.")
    elif menuType not in validTypes:
      await ctx.send("**Sorry, but you must include a valid role menu type.** Please specify either single or multi then try again.")
    elif persist not in validPersists:
      await ctx.send("**Sorry, but you must specify whether role selections should persist.** Please include either yes or no then try again.")
    else:
      await ctx.send("**Sorry, but I can't interpret your formatting.** Please ensure each option is surrounded by quotation marks, then try again.")

  @commands.command()
  @commands.guild_only()
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

    while args.find('"', start) != -1:
      start = args.find('"', start) + 1
      end = args.find('"', start)
      role = ctx.guild.get_role(int(args[(start + 3):(end - 1)]))
      roles.append(role)
      numOfRoles += 1
      start = end + 1

    start = rolesStart
    emojis = []
    start += 1
    i = 0
    while i <= numOfRoles:
      end = args.find('"', start) - 1
      if args[start:end] != "":
          emojis.append(args[start:end])
      start = args.find('"', end)
      start = args.find('"', start + 1) + 2
      i += 1

    validTypes = ["single", "multi"]
    validPersists = ["yes", "no"]

    numOfReactions = 0
    roleMenu = await ctx.channel.fetch_message(menuID)
    if roleMenu.reactions:
      for reaction in roleMenu.reactions:
        if str(reaction.emoji) in emojis:
          numOfReactions += 1

    numOfRoles = len(roles)
    numOfEmojis = len(emojis)
    keySuffix = str(ctx.guild.id) + "-" + name

    # If there is at least 2 options each with their own emoji, proceed to save the menu.
    # Otherwise, determine the error and send the appropriate error message
    if (("ID For Menu " + keySuffix) not in db) and (((menuType in validTypes) and (persist in validPersists)) and ((((numOfRoles + numOfEmojis)) % 2) == 0)) and ((numOfRoles <= 20) and (numOfEmojis <= 20)):
      # Save the role menu's information so it behaves like a standard GlitchBot menu
      db["ID For Menu " + keySuffix] = menuID
      db["Creator ID For Menu " + keySuffix] = ctx.message.author.id
      db["Emojis For Menu " + keySuffix] = emojis

      roleIDs = []
      for role in roles:
        roleIDs.append(role.id)

      db["Role IDs For Menu " + keySuffix] = roleIDs
      db["Type For Menu " + keySuffix] = menuType
      db["Persist For Menu " + keySuffix] = persist

      for emoji in emojis:
        await roleMenu.add_reaction(emoji)

      await ctx.send("**Role menu successfully converted!**")

    elif ("ID For Menu " + keySuffix) in db:
      await ctx.send("**Sorry, but a menu with that name already exists!** Try a new name or delete/strip the original menu (deleteMenu <name>) then try again.")
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
  @commands.guild_only()
  @commands.check(isAdminOrAbove)
  async def removeMenu(self, ctx, *, name):
    name = clearPunctuation(name)
    keySuffix = str(ctx.guild.id) + "-" + name

    # Check that the person attempting to remove the menu is the creator or an owner
    if ((("ID For Menu " + keySuffix) in db) and (db["ID For Menu " + keySuffix] != None)) and ((ctx.message.author.id == ctx.guild.owner_id) or (ctx.message.author.id == db["Creator ID For Menu " + keySuffix])):
      roleMenu = await ctx.channel.fetch_message(db["ID For Menu " + keySuffix])

      # Remove all bot reactions from the message TODO figure out why tf it isn't working
      bot = await ctx.guild.fetch_member(789322945285718066)
      for emoji in db["Emojis For Menu " + keySuffix]:
        await roleMenu.remove_reaction(emoji, bot)

      # If persist is off, delete all the selected roles
      if db["Persist For Menu " + keySuffix] == "no":
        index = 0
        for reaction in roleMenu.reactions:
          reactionUsers = await reaction.users().flatten()
          for reactionUser in reactionUsers:
            if not reactionUser.bot:
              removeRole = ctx.guild.get_role(db["Role IDs For Menu " + keySuffix][index])
              await reactionUser.remove_roles(removeRole)
          index += 1

      # Clear all menu data from the database
      del db["ID For Menu " + keySuffix]
      del db["Creator ID For Menu " + keySuffix]
      del db["Emojis For Menu " + keySuffix]
      del db["Role IDs For Menu " + keySuffix]
      del db["Type For Menu " + keySuffix]
      del db["Persist For Menu " + keySuffix]

      await ctx.send(f"**{name} is no longer a role menu.**")
    elif ctx.message.author.id != db["Creator ID For Menu " + keySuffix]:
      await ctx.send("**Sorry, but you must be the menu's creator to remove it.**")
    elif ("ID For Menu " + keySuffix) not in db:
      await ctx.send("**Sorry, but I can't find a role menu with that name!** Check that the menu exists and you are spelling its name correctly.")
    elif db["ID For Menu " + keySuffix] == None:
      await ctx.send("**Sorry, but that role menu has already been removed or deleted!**")

  # Role menu deletion command
  @commands.command()
  @commands.guild_only()
  @commands.check(isAdminOrAbove)
  async def deleteMenu(self, ctx, *, name):
    name = clearPunctuation(name)
    keySuffix = str(ctx.guild.id) + "-" + name

    # Check that the person attempting to delete the menu is the creator or an owner
    if ((("ID For Menu " + name) in db) and (db["ID For Menu " + name] != None)) and ((ctx.message.author.id == ctx.guild.owner_id) or (ctx.message.author.id == db["Creator ID For Menu " + name])):
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
      
      # Clear all menu data from the database
      del db["ID For Menu " + keySuffix]
      del db["Creator ID For Menu " + keySuffix]
      del db["Emojis For Menu " + keySuffix]
      del db["Role IDs For Menu " + keySuffix]
      del db["Type For Menu " + keySuffix]
      del db["Persist For Menu " + keySuffix]

      await ctx.send(f"**{name} role menu was deleted.**")
    elif ctx.message.author.id != db["Creator ID For Menu " + name]:
      await ctx.send("**Sorry, but you must be the menu's creator to delete it.**")
    elif ("ID For Menu " + name) not in db:
      await ctx.send("**Sorry, but I can't find a role menu with that name!** Check that the menu exists and you are spelling its name correctly.")
    elif db["ID For Menu " + name] == None:
      await ctx.send("**Sorry, but that role menu has already been removed or deleted!**")
  
  """
  @commands.command()
  async def debugMenu(self, ctx, *, args: str):
    start = 0
    end = 0
    i = 1
    
    # Obtain the menu's metadata by parsing the first three substrings
    start = args.find('"', start) + 1
    end = args.find('"', start)
    menuID = int(args[start:end])

    # Create an emoji and option list by parsing the remaining portion of the string
    emojis = []
    start = end + 2
    i = 0
    numOfRoles = 12
    while i <= numOfRoles:
      end = args.find('"', start) - 1
      if args[start:end] != "":
        emojis.append(args[start:end])
      start = args.find('"', end)
      start = args.find('"', start + 1) + 2
      i += 1

    numOfReactions = 0
    roleMenu = await ctx.channel.fetch_message(menuID)
    print(f"Menu ID: {menuID}")
    if roleMenu.reactions:
      print(f"Emojis expected: {emojis}")
      print(f"Num of emojis expected: {len(emojis)}")
      for reaction in roleMenu.reactions:
        print(f"Reaction retrieved: {str(reaction.emoji)}")
        print(f"Reaction {str(reaction.emoji)} in emojis? {str(reaction.emoji) in emojis}")
        if str(reaction.emoji) in emojis:
          numOfReactions += 1
      
      print(f"Reactions found: {numOfReactions}")
  """
def setup(client):
  client.add_cog(Interactive(client))