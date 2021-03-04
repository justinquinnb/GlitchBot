import discord
from discord.ext import commands
from replit import db

# Denotes this code as a class of commands under the name General and initializes it
class Developer(commands.Cog):
  def __init__(self, client):
    self.client = client

    # Gives this cog the attributes needed for the auto help command.
    self.parameters = ["<channelID>", "<message>"]

    self.shortDescs = ["Sets the puppet stage.", "Puppets the bot."]

    self.longDescs = [
      "Allows developers to set the channel in which puppet messages will be sent to.",
      "Allows developers to send the included message to the stage channel as a gag."]

    self.paramDescs = [
    "`<channelID>` The ID of the channel to set as the stage.",
    "`<message>` The message you would like to send to the channel."]

    self.restrictions = ["Only developers", "Only developers"]

<<<<<<< HEAD:cogs/5developer.py
  # Check for admin level or above
  def isDev(ctx):
    devs = [335440648393981952, 485182871867359255, 326453148178710530]
    return ctx.message.author.id in devs

=======
>>>>>>> origin/master:cogs/4developer.py
  # Gag puppet staging command
  @commands.command()
  @commands.check(isDev)
  async def puppetStage(self, ctx, serverID: int, channelID: int):
    try:
      db["Puppet Stage Channel ID"] = channelID
      db["Puppet Stage Server ID"] = serverID

      server = self.client.get_guild(serverID)
      channel = server.get_channel(channelID)
      await ctx.send(f"**Puppet stage set to the {channel.name} channel in {server.name}**")
    except:
      await ctx.send("**You must include valid server and channel IDs!**")

  # Gag puppet command
  @commands.command()
  @commands.check(isDev)
  async def puppet(self, ctx, *, text: str):
    try:
      server = self.client.get_guild(db["Puppet Stage Server ID"])
      channel = server.get_channel(db["Puppet Stage Channel ID"])
      await channel.send(text)
    except:
      await ctx.send("**You must set the puppet stage!**")

def setup(client):
  client.add_cog(Developer(client))