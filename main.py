import os
import sys
import discord
import asyncio
import datetime
from discord.ext import commands
from replit import db

sys.path.insert(1, 'env/globalData')

from globalData import CommandInfo, GuildConfig, ordinal, randomCode, localize, dbUpload, getConfig, createConfig, updateConfig

# STARTUP ------------------------------------------------------------------
# Run the bot in development mode (adopt BetaBot functionality)
DEV_MODE = True

# Declare bot intents and establish bot's client
intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix=';;',
                      intents=intents,
                      help_command=None,
                      owner_id=os.getenv('JustinID'))

async def initiateBot():
    # Announce DEVMODE
    if DEV_MODE: print("[WARNING] DEVMODE IS ENABLED!")

    # Load JSON data
    print("[STARTUP] GlitchBot is starting up! Loading JSON data...")
    cInfo = {}
    localize("globalData/commandInfo.json", cInfo, CommandInfo)

    # Upload hardcoded data to the database
    print("[STARTUP] JSON data loaded. Uploading local data to database...")
    dbUpload("globalData/guildConfig.json", db, "Guild Config For ",
             GuildConfig)

    # Sync the database to reflect changes in key formatting or objects
    print("[STARTUP] Local data uploaded. Syncing database changes...")
    #--- dbSync

    # Reset data pertaining to force stops and database clears
    print("[STARTUP] Database successfully synced. Resetting session info...")

    db["forceStop Confirmed"] = False
    db["forceStop Confirmation Code"] = None
    db["forceStop Confirmation Message ID"] = None

    db["clearDB Confirmed"] = False
    db["clearDB Confirmation Code"] = None
    db["clearDB Confirmation Message ID"] = None

    # Obtain bot update info
    with open("globalData/updates.txt", "r") as file:
        content = file.readlines()
        db["Bot Version"] = content[0].strip()
        db["Update Date"] = content[1].strip()
    db["Last Restart"] = (datetime.date.today()).strftime("%x")

    # Declare bot information before sign-in
    print("[STARTUP] Session info reset. Loading cogs...")

    # Load all cogs in the cogs folder
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await client.load_extension(f'cogs.{filename[:-3]}')

    print("[STARTUP] Cogs loaded. Starting client...")


# On startup console log and status setter
@client.event
async def on_ready():
    # Sync command tree
    print(f"[STARTUP] Client has logged in as {client.user}. Syncing commands...")
    await client.tree.sync()
    
    print(
        f"[STARTUP] Commands synced. Startup completed at {(datetime.datetime.now()).strftime('%X on %x')}")
    print('-------------------------------------')

    # Set bot status upon sucessful login
    await client.change_presence(status=discord.Status.online,
                                 activity=discord.Activity(name="Computing"))

    # Change the bot's nickname in the development servers to reflect current usage
    devGuildIDs = [os.getenv('DevHub ID')]
    for guildID in devGuildIDs:
        devServer = client.get_guild(guildID)
        botMember = await devServer.fetch_member(client.user.id)
        await botMember.edit(nick="GlitchBot Beta (BB)")


# CHECKS ------------------------------------------------------------------
def isDev(ctx):
    devs = [os.getenv('Justin ID')]
    return ctx.message.author.id in devs


# EVENTS ------------------------------------------------------------------


# Sends an embed to the announcements channel on member join
@client.event
async def on_member_join(member):
    cfg = getConfig(member.guild.id)
    channel = member.guild.get_channel(cfg["infoChannel"])
    joinEmbed = discord.Embed(
        title=f"Welcome to {member.guild.name}, {member.name}!",
        color=cfg["positiveColor"])
    joinEmbed.set_author(
        name=
        f"{member.name} joined the server | {ordinal(len(member.guild.members))} member",
        icon_url=member.avatar_url)
    joinEmbed.set_thumbnail(
        url=
        "https://cdn.discordapp.com/attachments/796907538570412033/798607925882126346/memberjoin.png"
    )
    await channel.send(embed=joinEmbed)
    db["Warnings For " + str(member.id)] = 0


# Sends an embed to the announcements channel on member leave (self-leave or kick, not ban)
@client.event
async def on_member_remove(member):
    try:
        await member.guild.fetch_ban(member)
    except:
        cfg = getConfig(member.guild.id)
        channel = member.guild.get_channel(cfg["infoChannel"])
        leaveEmbed = discord.Embed(
            title=f"Bye, {member.name}! See you around!",
            color=cfg["negativeColor"])
        leaveEmbed.set_author(name=f"{member.name} left the server",
                              icon_url=member.avatar_url)
        leaveEmbed.set_thumbnail(
            url=
            "https://cdn.discordapp.com/attachments/796907538570412033/798608106057629766/memberleave.png"
        )
        await channel.send(embed=leaveEmbed)


# Sends an embed to the announcements channel on member ban
@client.event
async def on_member_ban(guild, member):
    cfg = getConfig(member.guild.id)
    channel = member.guild.get_channel(cfg["infoChannel"])
    banEmbed = discord.Embed(
        title=f"The almighty ban hammer has spoken. {member.name}, begone!",
        color=cfg["negativeColor"])
    banEmbed.set_author(name=f"{member.name} was banned",
                        icon_url=member.avatar_url)
    banEmbed.set_thumbnail(
        url=
        "https://cdn.discordapp.com/attachments/796907538570412033/798752034077671464/memberban.png"
    )
    await channel.send(embed=banEmbed)


# Begin bot configuration upon client join
@client.event
async def on_guild_join(guild):
    # Send the initial welcome embed
    welcomeEmbed = discord.Embed(
        title=f"Hi, I'm {client.user.name}! Thanks for inviting me!",
        description=
        f"Before I can begin, please take a moment to set me up using the `{client.command_prefix}config` command.",
        color=0x9a2ab0)

    db["Active Servers"] += 1
    welcomeEmbed.set_thumbnail(url=client.user.avatar_url)
    welcomeEmbed.add_field(name="Version:",
                           value=db["Bot Version"],
                           inline=True)
    welcomeEmbed.add_field(name="Last Update:",
                           value=db["Update Date"],
                           inline=True)
    welcomeEmbed.add_field(name="Servers:",
                           value=str(db["Active Servers"]),
                           inline=True)

    db[f"Config Step For {guild.id}"] = 0

    sysChannel = guild.system_channel
    await sysChannel.send(embed=welcomeEmbed)


# Delete all associated database data upon client removal
@client.event
async def on_guild_remove(guild):
    # All the information to delete upon client removal
    generalKeyPrefixes = [
        "Guild Config For ", "Config Step For ",
        "Personal Invite Pending For ", "Server Invite Pending For ",
        "ID For Event ", "Host ID For Event", "ID For Poll ",
        "Poller ID For Poll ", "Options For Poll ", "Emojis For Poll ",
        "ID For Menu ", "Creator ID For Menu ", "Emojis For Menu ",
        "Role IDs For Menu ", "Type For Menu ", "Persist For Menu ",
        "Ban Pending For ", "Warnings For "
    ]

    # Add guild IDs to each key
    fullKeyPrefixes = []
    for prefix in generalKeyPrefixes:
        fullKeyPrefixes.append(prefix + guild.id)

    # Delete all the keys with the narrowed-down prefixes
    for fullPrefix in fullKeyPrefixes:
        for keyToDelete in db.prefix(fullPrefix):
            del db[keyToDelete]

    db["Active Servers"] -= 1


# INITIAL GUILD config -------------------------------------------------------
@client.command()
@commands.guild_only()
async def config(ctx, arg=None):
    # Ensure it's the server owner using the command
    if ctx.message.author.id == ctx.guild.owner_id:
        # Begin the correct procedure depending on whether or not this is the command's first #2
        # use
        if f"Config Step For {ctx.guild.id}" in db:
            if db[f"Config Step For {ctx.guild.id}"] == 0:
                starterMessage = await ctx.send(
                    """Ok, let's get started!\n__-For each question, respond using the config command and your answer immediately after.__\n__-Remember, settings can be changed again at any time, so don't stress about mistakes!__"""
                )

                db[f"Starter Config Message For {ctx.guild.id}"] = starterMessage.id

                # Create a guild config object for the current guild
                createConfig(db, ctx.guild.id)

                lastMessage = await ctx.send(
                    f"""**First, let's set up your join, info, event, and VIP channels!**\n> What channel would you like bot-created invite links to send new users to?\n> *Example:* `{client.command_prefix}config #welcome`"""
                )

                db[f"Last Config Message For {ctx.guild.id}"] = lastMessage.id
                db[f"Config Step For {ctx.guild.id}"] = 1

            elif db[f"Config Step For {ctx.guild.id}"] == 1:
                # Store the join channel ID
                arg = ctx.guild.get_channel(int(arg[2:-1]))

                if type(arg) == discord.channel.TextChannel:
                    lastMessage = await ctx.fetch_message(
                        db[f"Last Config Message For {ctx.guild.id}"])
                    await lastMessage.delete()

                    updateConfig(db, ctx.guild.id, "joinChannel", arg.id)
                    lastMessage = await ctx.send(
                        f"""Got it! New users will be directed to the {arg.mention} when they join with an invite link I created.\n**What channel would you like me to send member join, leave, and ban messages to?**\n> *Example:* `{client.command_prefix}config #announcements`"""
                    )

                    db[f"Last Config Message For {ctx.guild.id}"] = lastMessage.id
                    db[f"Config Step For {ctx.guild.id}"] = 2
                else:
                    warning = await ctx.send(
                        "**Sorry, but that does not appear to be a valid channel.** Make sure you are using the # form of the channel, then try again."
                    )
                    await warning.delete(delay=3)

            elif db[f"Config Step For {ctx.guild.id}"] == 2:
                arg = ctx.guild.get_channel(int(arg[2:-1]))

                # Store the info channel ID
                if type(arg) == discord.channel.TextChannel:
                    lastMessage = await ctx.fetch_message(
                        db[f"Last Config Message For {ctx.guild.id}"])
                    await lastMessage.delete()

                    updateConfig(db, ctx.guild.id, "infoChannel", arg.id)
                    lastMessage = await ctx.send(
                        f"""Alrighty! Member join, leave, and ban messages will appear in {arg.mention}.\n**What channel would you like mod vote invites, bans and reports to appear?**\n> *Example:* `{client.command_prefix}config #vip-channel`"""
                    )

                    db[f"Last Config Message For {ctx.guild.id}"] = lastMessage.id
                    db[f"Config Step For {ctx.guild.id}"] = 3
                else:
                    warning = await ctx.send(
                        "**Sorry, but that does not appear to be a valid channel.** Make sure you are using the # form of the channel, then try again."
                    )
                    await warning.delete(delay=3)

            elif db[f"Config Step For {ctx.guild.id}"] == 3:
                arg = ctx.guild.get_channel(int(arg[2:-1]))

                # Store the VIP channel ID
                if type(arg) == discord.channel.TextChannel:
                    lastMessage = await ctx.fetch_message(
                        db[f"Last Config Message For {ctx.guild.id}"])
                    await lastMessage.delete()

                    updateConfig(db, ctx.guild.id, "vipChannel", arg.id)
                    lastMessage = await ctx.send(
                        f"""Sounds good! Mod vote invites, bans, and reports will appear in {arg.mention}.\n**Finally, what channel would you like your server's events to appear in?**\n> *Example:* `{client.command_prefix}config #events`"""
                    )

                    db[f"Last Config Message For {ctx.guild.id}"] = lastMessage.id
                    db[f"Config Step For {ctx.guild.id}"] = 4
                else:
                    warning = await ctx.send(
                        "**Sorry, but that does not appear to be a valid channel.** Make sure you are using the # form of the channel, then try again."
                    )
                    await warning.delete(delay=3)

            elif db[f"Config Step For {ctx.guild.id}"] == 4:
                arg = ctx.guild.get_channel(int(arg[2:-1]))

                # Store the event channel ID
                if type(arg) == discord.channel.TextChannel:
                    lastMessage = await ctx.fetch_message(
                        db[f"Last Config Message For {ctx.guild.id}"])
                    await lastMessage.delete()

                    updateConfig(db, ctx.guild.id, "eventChannel", arg.id)
                    lastMessage = await ctx.send(
                        f"""Awesome! Your server's events will appear in {arg.mention}.\n**We're halfway there! Now onto your server's roles...**\n> What role should I consider to be your "mod" role? (Admins will be next)\n> *Example:* `{client.command_prefix}config @Mods`"""
                    )

                    db[f"Last Config Message For {ctx.guild.id}"] = lastMessage.id
                    db[f"Config Step For {ctx.guild.id}"] = 5
                else:
                    warning = await ctx.send(
                        "**Sorry, but that does not appear to be a valid channel.** Make sure you are using the # form of the channel, then try again."
                    )
                    await warning.delete(delay=3)

            elif db[f"Config Step For {ctx.guild.id}"] == 5:
                arg = ctx.guild.get_role(int(arg[3:-1]))

                # Store the mod role ID
                if type(arg) == discord.Role:
                    lastMessage = await ctx.fetch_message(
                        db[f"Last Config Message For {ctx.guild.id}"])
                    await lastMessage.delete()

                    updateConfig(db, ctx.guild.id, "modRole", arg.id)
                    lastMessage = await ctx.send(
                        f"""Great! I will consider those with the {arg.mention} role mods.\n**Now what role should I consider to be your "admin" role?**\n> *Example:* `{client.command_prefix}config @admins`"""
                    )

                    db[f"Last Config Message For {ctx.guild.id}"] = lastMessage.id
                    db[f"Config Step For {ctx.guild.id}"] = 6
                else:
                    warning = await ctx.send(
                        "**Sorry, but that does not appear to be a valid role.** Make sure you are using the @ form of the role, then try again."
                    )
                    await warning.delete(delay=3)

            elif db[f"Config Step For {ctx.guild.id}"] == 6:
                arg = ctx.guild.get_role(int(arg[3:-1]))

                # Store the admin role ID
                if type(arg) == discord.Role:
                    lastMessage = await ctx.fetch_message(
                        db[f"Last Config Message For {ctx.guild.id}"])
                    starterMessage = await ctx.fetch_message(
                        db[f"Starter Config Message For {ctx.guild.id}"])
                    await lastMessage.delete()
                    await starterMessage.delete()

                    updateConfig(db, ctx.guild.id, "AdminRole", arg.id)
                    lastMessage = await ctx.send(
                        f"Perfect! I will consider those with the {arg.mention} role.\n**Configuration complete! {client.user.name} is now set up and ready to go!**\n> If you'd like to change your config, use the `{client.command_prefix}config` command again at any time.\n> Other than that, try the `{client.command_prefix}help` command to see all that I can do!"
                    )

                    # Delete the temporary config key
                    del db[f"Config Step For {ctx.guild.id}"]
                else:
                    warning = await ctx.send(
                        "**Sorry, but that does not appear to be a valid role.** Make sure you are using the @ form of the role, then try again."
                    )
                    await warning.delete(delay=3)

            # !!!!!!!!CURRENTLY DISABLED!!!!!!!!
            elif db[f"Config Step For {ctx.guild.id}"] == -6:
                arg = ctx.guild.get_role(int(arg[3:-1]))

                # Store the admin role ID
                if type(arg) == discord.Role:
                    lastMessage = await ctx.fetch_message(
                        db[f"Last Config Message For {ctx.guild.id}"])
                    await lastMessage.delete()

                    db[f"Guild Config For {ctx.guild.id}"][
                        "adminRole"] = arg.id
                    lastMessage = await ctx.send(
                        f"""Okay! I will consider those with the {arg.mention} role admins.\n**We're almost done! Let's finish off with emojis...**\n> Which emoji should I consider to be your "yes" emoji?\n> *Example:* `{client.command_prefix}config :thumbsup:`"""
                    )

                    db[f"Last Config Message For {ctx.guild.id}"] = lastMessage.id
                    db[f"Config Step For {ctx.guild.id}"] = 7
                else:
                    warning = await ctx.send(
                        "**Sorry, but that does not appear to be a valid role.** Make sure you are using the @ form of the role, then try again."
                    )
                    await warning.delete(delay=3)

            elif db[f"Config Step For {ctx.guild.id}"] == -7:
                try:
                    arg = await ctx.guild.fetch_emoji(int(arg[2:-1]))
                except:
                    pass

                print(type(arg))

                # Store the yes emoji ID
                if type(arg) == discord.Emoji:
                    lastMessage = await ctx.fetch_message(
                        db[f"Last Config Message For {ctx.guild.id}"])
                    await lastMessage.delete()

                    db[f"Guild Config For {ctx.guild.id}"]["yesEmoji"] = arg.id
                    lastMessage = await ctx.send(
                        f"""Good choice! I will consider {arg} to be your "yes" emoji.\n**What should I consider to be your "no" emoji?**\n> *Example:* `{client.command_prefix}config :thumbsdown:`"""
                    )

                    db[f"Last Config Message For {ctx.guild.id}"] = lastMessage.id
                    db[f"Config Step For {ctx.guild.id}"] = 8
                else:
                    warning = await ctx.send(
                        "**Sorry, but that does not appear to be a valid emoji.** Make sure it is a proper emoji, then try again."
                    )
                    await warning.delete(delay=3)

            elif db[f"Config Step For {ctx.guild.id}"] == -8:
                try:
                    arg = await ctx.guild.fetch_emoji(int(arg[2:-1]))
                except:
                    pass

                # Store the no emoji ID
                if type(arg) is discord.Emoji:
                    lastMessage = await ctx.fetch_message(
                        db[f"Last Config Message For {ctx.guild.id}"])
                    await lastMessage.delete()

                    db[f"Guild Config For {ctx.guild.id}"]["noEmoji"] = arg.id
                    lastMessage = await ctx.send(
                        f"""Great choice! I will consider {arg} to be your "no" emoji.\n**Last but not least, what should I consider to be your "maybe" emoji?**\n> *Example:* `{client.command_prefix}config :person_shrugging:`"""
                    )

                    db[f"Last Config Message For {ctx.guild.id}"] = lastMessage.id
                    db[f"Config Step For {ctx.guild.id}"] = 9
                else:
                    warning = await ctx.send(
                        "**Sorry, but that does not appear to be a valid emoji.** Make sure it is a proper emoji, then try again."
                    )
                    await warning.delete(delay=3)

            elif db[f"Config Step For {ctx.guild.id}"] == -9:
                try:
                    arg = await ctx.guild.fetch_emoji(int(arg[2:-1]))
                except:
                    pass

                # Store the maybe emoji ID
                if type(arg) is discord.Emoji:
                    lastMessage = await ctx.fetch_message(
                        db[f"Last Config Message For {ctx.guild.id}"])
                    starterMessage = await ctx.fetch_message(
                        db[f"Starter Config Message For {ctx.guild.id}"])
                    await lastMessage.delete()
                    await starterMessage.delete()

                    db[f"Guild Config For {ctx.guild.id}"][
                        "maybeEmoji"] = arg.id
                    db[f"Last Config Message For {ctx.guild.id}"] = await ctx.send(
                        f"""Perfect! I will consider {arg} to be your "maybe" emoji.\n**Configuration complete! {client.user.name} is now set up and ready to go!**\n> If you'd like to change your config, use the `{client.command_prefix}config` command again at any time.\n> Other than that, try the `{client.command_prefix}help` command to see all that I can do!"""
                    )

                    # Delete the temporary config key
                    del db[f"Config Step For {ctx.guild.id}"]

                else:
                    warning = await ctx.send(
                        "**Sorry, but that does not appear to be a valid emoji.** Make sure it is a proper emoji, then try again."
                    )
                    await warning.delete(delay=3)

        else:
            await ctx.send(
                "**Sorry, but non-initiative usage of this command is not yet complete. Please try again later.**"
            )

    else:
        await ctx.send(
            "**Sorry, but only the server owner can configure the bot.** Please contact them if there's a problem."
        )


# COMMANDS ------------------------------------------------------------------
@client.tree.command(name="test")
async def test(interaction: discord.Interaction):
    print("Test received!")
    await interaction.response.send_message("Test received!")


# Command for force stopping the bot
@client.command()
@commands.check(isDev)
async def forceStop(ctx, inputCode: str = None):
    # If a force stop is not already in progress, reset force stop info and initiate the process
    if inputCode == None and (("forceStop Confirmation Code" not in db) or
                              (db["forceStop Confirmation Code"] == None)):
        # Reset database info regarding the force stop process
        db["forceStop Confirmed"] = False
        db["forceStop Confirmation Code"] = randomCode(6)
        db["forceStop Confirmation Message ID"] = None

        # Log the initiation and message the channel with confirmation instructions
        print("Force stop initiated by " + ctx.message.author.display_name +
              ". Code: " + db["forceStop Confirmation Code"])
        confirmation = await ctx.send(
            f"**You are about to force stop {client.user.name}**. Send the command again with the code...\n`{db['forceStop Confirmation Code']}`\n...to confirm. The code expires in **10** seconds."
        )
        db["forceStop Confirmation Message ID"] = confirmation.id

        # Begin the countdown
        countdown = 10

        # Update the countdown message as time runs out
        while countdown >= 1:
            await asyncio.sleep(1)
            countdown -= 1
            if not db["forceStop Confirmed"]:
                await confirmation.edit(
                    content=
                    f"**You are about to force stop {client.user.name}**. Send the command again with the code...\n`{db['forceStop Confirmation Code']}`\n...to confirm. The code expires in **{str(countdown)}** seconds."
                )

        # If the force stop wasn't confirmed by the end of the countdown, update the message
        if not db["forceStop Confirmed"]:
            db["forceStop Confirmation Code"] = None
            print("Force stop cancelled.")
            await confirmation.edit(
                content=
                "**The code has expired.** Re-enter the `;;forceStop` command to try again"
            )

    # Alert the user the user that a force stop is already in progress upon a re-initiation
    # attempt
    elif inputCode == None and db["forceStop Confirmation Code"] != None:
        await ctx.send(
            f"**Confirmation in progress!** Please enter the code `{db['forceStop Confirmation Code']}` to confirm!"
        )

    # If the user enters the correct confirmation code, prevent the bot from receiving the
    # uptime ping and send/log a success message
    elif inputCode == db["forceStop Confirmation Code"] and db[
            "forceStop Confirmation Code"] != None:
        cfg = getConfig(ctx.guild.id)
        db["forceStop Confirmed"] = True
        confirmation = await ctx.fetch_message(
            db["forceStop Confirmation Message ID"])
        print(f"Force stop confirmed by {ctx.message.author.display_name}!")
        await confirmation.edit(
            content="**Bot force stop confirmed.** The code is no longer usable."
        )
        confirmationEmbed = discord.Embed(
            title="Bot will shut down within 5 minutes...",
            color=cfg["negativeColor"])
        confirmationEmbed.set_author(
            name=f"Force stop confirmed by {ctx.message.author.display_name}.",
            icon_url=ctx.message.author.avatar_url)
        confirmationEmbed.set_thumbnail(
            url=
            "https://cdn.discordapp.com/attachments/796907538570412033/800209126550011904/forcestop.png"
        )

        await client.change_presence(status=discord.Status.do_not_disturb,
                                     activity=discord.Game("Shutting down..."))
        await ctx.send(embed=confirmationEmbed)
        await ctx.send(
            "**BetaBot cannot be force stopped as it does not run on the same system as GlitchBot!** However, the development session will time out after 5 minutes of inactivity anyway."
        )


# Command for clearing the bot's database
@client.command()
@commands.check(isDev)
async def clearDB(ctx, inputCode: str = None):
    # If a database clear is not already in progress, reset db clear info and initiate
    # the process
    if inputCode == None and (("clearDB Confirmation Code" not in db) or
                              (db["clearDB Confirmation Code"] == None)):
        # Reset database info regarding the force stop process
        db["clearDB Confirmed"] = False
        db["clearDB Confirmation Code"] = randomCode(6)
        db["clearDB Confirmation Message ID"] = None

        # Log the initiation and message the channel with confirmation instructions
        print("Database clear initiated by " +
              ctx.message.author.display_name + ". Code: " +
              db["clearDB Confirmation Code"])
        confirmation = await ctx.send(
            f"**You are about to clear the {client.user.name} database**. Send the command again with the code...\n`{db['clearDB Confirmation Code']}`\n...to confirm. The code expires in **10** seconds."
        )
        db["clearDB Confirmation Message ID"] = confirmation.id

        # Begin the countdown
        countdown = 10

        # Update the countdown message as time runs out
        while countdown >= 1:
            await asyncio.sleep(1)
            countdown -= 1
            if not db["clearDB Confirmed"]:
                await confirmation.edit(
                    content=
                    f"**You are about to clear the {client.user.name} database**. Send the command again with the code...\n`{db['clearDB Confirmation Code']}`\n...to confirm. The code expires in **{str(countdown)}** seconds."
                )

        # If the database clear wasn't confirmed by the end of the countdown, update
        # the message
        if not db["clearDB Confirmed"]:
            db["clearDB Confirmation Code"] = None
            print("Database clear cancelled.")
            await confirmation.edit(
                content=
                "**The code has expired.** Re-enter the `;;clearDB` command to try again"
            )

    # Alert the user the user that a database clear is already in progress upon
    # a re-initiation attempt
    elif inputCode == None and db["clearDB Confirmation Code"] != None:
        await ctx.send(
            f"**Confirmation in progress!** Please enter the code `{db['clearDB Confirmation Code']}` to confirm!"
        )

    # If the user enters the correct confirmation code, clear the bot's database
    elif inputCode == db["clearDB Confirmation Code"] and db[
            "clearDB Confirmation Code"] != None:
        cfg = getConfig(ctx.guild.id)
        db["clearDB Confirmed"] = True
        confirmation = await ctx.fetch_message(
            db["clearDB Confirmation Message ID"])
        print(
            f"Database clear confirmed by {ctx.message.author.display_name}!")
        await confirmation.edit(
            content="**Database clear confirmed.** The code is no longer usable."
        )
        confirmationEmbed = discord.Embed(
            title="The database will be cleared shortly...",
            color=cfg["negativeColor"])
        confirmationEmbed.set_author(
            name=
            f"Database clear confirmed by {ctx.message.author.display_name}.",
            icon_url=ctx.message.author.avatar_url)
        confirmationEmbed.set_thumbnail(
            url=
            "https://cdn.discordapp.com/attachments/796907538570412033/815426922052845578/dbclear.png"
        )

        await ctx.send(embed=confirmationEmbed)

        # Delete all the keys from the database except the ones which are always problematic
        problemKeys = [
            "clearDB Confirmed",
            "ID For Poll How long can I make this poll before it breaks?",
            "Options for Poll How long can I make this poll before it breaks?",
            "Poller ID For Poll How long can I make this poll before it breaks?"
        ]
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
            print(
                f"{ctx.message.author.name} unloaded the {cogName.title()} cog."
            )
            await ctx.send(f"**Unloaded cog:** {cogName.title()}")
        else:
            await ctx.send("**The specified cog does not exist.**")
    except:
        if isinstance(unloadCog.error, commands.MissingRole):
            await ctx.send(
                "**Sorry, but only developers are allowed to do that!**")
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
            print(
                f"{ctx.message.author.name} loaded the {cogName.title()} cog.")
            await ctx.send(f"**Loaded cog:** {cogName.title()}")
        else:
            await ctx.send("**The specified cog does not exist.**")
    except:
        if isinstance(loadCog.error, commands.MissingRole):
            await ctx.send(
                "**Sorry, but only developers are allowed to do that!**")
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
            if (filename.endswith('.py') and
                (filename[:-3] != "developer")) and ((filename[:-3] in str(
                    client.cogs.values()))):
                client.unload_extension(f'cogs.{filename[:-3]}')
                anythingUnloaded = True

        if anythingUnloaded:
            print(f"{ctx.message.author.name} unloaded all cogs.")
            await ctx.send("**All cogs are now unloaded.**")
        else:
            await ctx.send("**All cogs are already unloaded.**")
    except:
        if isinstance(unloadCogs.error, commands.MissingRole):
            await ctx.send(
                "**Sorry, but only developers are allowed to do that!**")


@client.command()
@commands.check(isDev)
async def loadCogs(ctx):
    try:
        # Load all cogs which have not already been loaded, then send a message specifying what was
        # done
        anythingLoaded = False
        for filename in os.listdir('./cogs'):
            if (filename.endswith('.py') and
                (filename[:-3] != "developer")) and ((filename[:-3] not in str(
                    client.cogs.values()))):
                client.load_extension(f'cogs.{filename[:-3]}')
                anythingLoaded = True

        if anythingLoaded:
            print(f"{ctx.message.author.name} loaded all cogs.")
            await ctx.send("**Successfully loaded all cogs.**")
        else:
            await ctx.send("**All cogs are already loaded.**")
    except:
        if isinstance(loadCogs.error, commands.MissingRole):
            await ctx.send(
                "**Sorry, but only developers are allowed to do that!**")


# Smart help command that automatically catalogues loaded cogs and commands
@client.command()
async def help(ctx, inputCommand: str = None):
    cfg = getConfig(ctx.guild.id)

    # Use the correct prefix for the bot
    prefix = client.command_prefix
    mainGroups = ["Developer", "General"]
    mainCommands = [
        "forceStop", "clearDB", "unloadCog", "unloadCogs", "loadCog",
        "loadCogs", "help"
    ]

    if inputCommand == None:
        # Set up the base help embed
        helpEmbed = discord.Embed(
            title="Here's a list of commands:",
            description=
            "Required parameters in <>. Optional parameters in ().",
            url=
            "https://docs.google.com/document/d/1bXniMEdQ1p0rBe5EJsHFVl-8AL8huo2FJ0qL7ANBeTU/edit?usp=sharing",
            color=cfg["generalColor"])

        # Here, cog refers to the groups of commands located outside this file. Group names
        # are for commands which belong in a cog, but are located in this file. All cogs are
        # groups, but not all groups are cogs in this case.

        # Ensure the help command is displayed regardless of whether or not the general cog
        # is loaded
        if "General" not in client.cogs:
            helpEmbed.add_field(
                name="General",
                value=f"`{prefix}help (commandName)` Displays command info.",
                inline=False)

        # Iterate through all the loaded cogs
        for cogName in client.cogs:
            cog = client.get_cog(cogName)

            # If the cog has commands or there is a command within main.py that belongs to that
            # group, add those commands to the list
            if (len(cog.get_commands()) != 0) or (cogName in mainGroups):
                # This string variable will house all the commands and their information for every
                # group
                commandList = ""

                # If there is a command in main.py that belongs to the cog we're currently
                # registering, add it
                if cogName in mainGroups:
                    commandNum = 0
                    # Scan through all the commands in main.py and add the ones that belong to the
                    # cog we're currently registering
                    for commandName in mainCommands:
                        currentCommand = cInfo[mainCommands[commandNum]]
                        # If the command belongs to a group/cog which is loaded, add it
                        if currentCommand.group == cogName:
                            if currentCommand.params != "":
                                commandList = commandList + f"`{prefix}" + currentCommand.name + " " + currentCommand.params + "` " + currentCommand.shortDesc + "\n"
                            else:
                                commandList = commandList + f"`{prefix}" + currentCommand.name + "` " + currentCommand.shortDesc + "\n"

                        commandNum += 1

                # Add all the commands from the actual cog to the help string
                for command in cog.get_commands():
                    # Format the command appropriately depending on whether or not it contains parameters
                    currentCommand = cInfo[str(command)]
                    if currentCommand.params != "":
                        commandList = commandList + f"`{prefix}" + currentCommand.name + " " + currentCommand.params + "` " + currentCommand.shortDesc + "\n"
                    else:
                        commandList = commandList + f"`{prefix}" + currentCommand.name + "` " + currentCommand.shortDesc + "\n"

                # Finish this group of commands off by adding it to the help embed as a new field
                helpEmbed.add_field(name=cogName.title() + ":",
                                    value=commandList,
                                    inline=False)

        # Complete the embed by adding a thumbnail and WIP footer, then send it to the
        # requested channel
        helpEmbed.set_thumbnail(
            url=
            "https://cdn.discordapp.com/attachments/796907538570412033/799741594701922354/help.png"
        )
        helpEmbed.set_footer(
            text=
            "For a full guide on GlitchBot's commands, click the link above")
        await ctx.send(embed=helpEmbed)
    else:
        # Send help information if the specified command is valid. Otherwise, send an error message
        if inputCommand in cInfo.keys():
            command = cInfo[inputCommand]

            # Retrieve the specified command information and add it to an embed
            if command.params != "":
                helpEmbed = discord.Embed(
                    title=f"{prefix}{command.name} {command.params}",
                    color=cfg["generalColor"])
            else:
                helpEmbed = discord.Embed(title=f"{prefix}{command.name}",
                                          color=cfg["generalColor"])

            helpEmbed.add_field(name="Example:",
                                value=f"`{prefix}{command.example}`",
                                inline=False)
            helpEmbed.add_field(name="Description:",
                                value=command.longDesc,
                                inline=False)

            if command.paramDescs != "":
                helpEmbed.add_field(name="Parameters:",
                                    value=command.paramDescs,
                                    inline=False)

            if command.restrictions != "":
                helpEmbed.add_field(
                    name="Restrictions:",
                    value=f"{command.restrictions} can use this command.",
                    inline=False)
            else:
                helpEmbed.add_field(name="Restrictions:",
                                    value="Anyone can use this command.",
                                    inline=False)

            helpEmbed.set_thumbnail(
                url=
                "https://cdn.discordapp.com/attachments/796907538570412033/799741594701922354/help.png"
            )
            helpEmbed.set_footer(
                text=
                "This bot is currently a WIP. Commands are subject to change.")
            await ctx.send(embed=helpEmbed)
        else:
            await ctx.send(
                "**Sorry, but the specified command is either disabled or does not exist.**"
            )


# Start the bot
asyncio.run(initiateBot())
asyncio.run(
    client.start(
        os.getenv("BetaBot API Token" if DEV_MODE else "GlitchBot API Token")))