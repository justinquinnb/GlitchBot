import discord
from discord.ext import commands
from replit import db

# Denotes this code as a class of commands under the name General and initializes it
class Developer(commands.Cog):
  def __init__(self, client):
    self.client = client

  # Check for admin level or above
  def isDev(ctx):
    devs = [335440648393981952, 485182871867359255, 326453148178710530]
    return ctx.message.author.id in devs

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