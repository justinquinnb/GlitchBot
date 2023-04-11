import json

class GuildConfig:
  def __init__(
      self,
      name, # Guild name (secondary identifier)
      guildID, # Guild id (primary identifier, can be used to check key/value alignment)
      positiveColor, # Color for "good" actions
      negativeColor, # Color for "bad" actions
      generalColor, # Color for general, netural actions
      infoChannel, # ID for join/leave/ban/etc. message channel
      joinChannel, # ID for channel approved invite links will direct to
      vipChannel, # ID for mod/admin exclusive channel
      eventChannel, # ID for server events channel
      modRole, # ID for mod role or equivelant
      adminRole, # ID for admin role or equivelant
      yesEmoji, # ID for yes emoji
      noEmoji, # ID for no emoji
      maybeEmoji # ID for maybe emoji
  ):
    self.name = name 
    self.guildID = guildID 
    self.positiveColor = positiveColor # Automatically typecast these at some point
    self.negativeColor = negativeColor
    self.generalColor = generalColor 
    self.infoChannel = infoChannel
    self.joinChannel = joinChannel
    self.vipChannel = vipChannel
    self.eventChannel = eventChannel
    self.modRole = modRole 
    self.adminRole = adminRole 
    self.yesEmoji = yesEmoji
    self.noEmoji = noEmoji
    self.maybeEmoji = maybeEmoji
  
  @classmethod
  def fetch(cls, jsonFileName, index):
    with open(jsonFileName, 'r') as jsonFile:
      jsonDict = json.load(jsonFile)
    
    return cls(**jsonDict["GuildConfig"][index])

class CommandInfo:
  def __init__(
      self,
      name, # The name of the command without prefix or params
      group, # The commands group (or cog if applicable)
      params, # String containing all of the command's parameters
      example, # An example of command usage
      shortDesc, # A short description of the command for use in the general help command
      longDesc, # A longer description of the command for use in the specific help command
      paramDescs, # String containing brief descriptions of each parameter
      restrictions # A string containing role restrictions
  ):
    self.name = name 
    self.group = group
    self.params = params
    self.example = example
    self.shortDesc = shortDesc
    self.longDesc = longDesc
    self.paramDescs = paramDescs
    self.restrictions = restrictions
  
  @classmethod
  def fetch(cls, jsonFileName, index):
    with open(jsonFileName, 'r') as jsonFile:
      jsonDict = json.load(jsonFile)
    
    return cls(**jsonDict["CommandInfo"][index])