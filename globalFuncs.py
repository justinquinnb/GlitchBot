import json
import string
import random
from replit import db

debug = False

# UTILITY FUNCTIONS-------------------------------------------------------------

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

# Generates a random letter and number code
def randomCode(length):
  # List of characters [a-zA-Z0-9]
  chars = string.ascii_letters + string.digits
  code = ''.join(random.choice(chars) for _ in range(length))
  return code

# Generates a 6 digit ticket number and formats it correctly
def ticketCode(database, variant):
  variant = variant.title()
  ticketNum = database[f"{variant} Ticket Number"] + 1
  database[f"{variant} Ticket Number"] += 1

  # Format the number correctly as a string
  numOfZeros = 0
  ticketString = str(ticketNum)

  numLength = 6
  if len(ticketString) > 6:
    numLength = len(ticketString)

  while numOfZeros < (numLength - len(str(ticketNum))):
    ticketString = "0" + ticketString
    numOfZeros += 1
  
  return ticketString


# Function for removing punctuation from parts of db keys
def clearPunctuation(string):
  punctuation = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
  for character in string:
    if character in punctuation:
      string = string.replace(character, "")
  
  return string

# CHECK FUNCTIONS-------------------------------------------------------------
def configCheck(ctx, reqConfigs):
  

# JSON FUNCTIONS--------------------------------------------------------------

# Map objects from the <className> class in the <fileName> file into the <dictName> dict
# Used to retrieve default server use settings
def localize(fileName, dictName, className):
  with open(fileName, 'r') as jsonFile:
    jsonDict = json.load(jsonFile)

  print("------------------------------------------------------------") if debug else exit
  numOfObjects = len(jsonDict[className.__name__])
  print(f"Localizing {className} | Object count: {numOfObjects}") if debug else exit
  index = 0
  while index < numOfObjects:
    pythonObject = className.fetch(fileName, index)
    dictName[pythonObject.name] = pythonObject
    print(f"Localizing {className} | Localized object:\n{pythonObject}\nat index {index}") if debug else exit
    index += 1

def dbUpload(fileName, database, prefix, className):
  with open(fileName, 'r') as jsonFile:
    jsonDict = json.load(jsonFile)
  
  numOfObjects = len(jsonDict[className.__name__])
  index = 0
  while index < numOfObjects:
    jsonObject = jsonDict[className.__name__][index]
    pythonObject = className.fetch(fileName, index)
    objectString = json.dumps(jsonObject)
    database[prefix + str(pythonObject.guildID)] = objectString
    index += 1

# Generate the database key to retrieve the guild's config object
def getConfig(guildID):
  # Create the dict first from the stored db JSON string
  configDict = json.loads(db[f"Guild Config For {str(guildID)}"])
  
  # Typecast certain values so they function correctly
  configDict["positiveColor"] = int(configDict["positiveColor"], 0)
  configDict["negativeColor"] = int(configDict["negativeColor"], 0)
  configDict["generalColor"] = int(configDict["generalColor"], 0)
  return configDict

def createConfig(database, guildID):
  with open("globalData/defaultConfig.json", 'r') as jsonFile:
    jsonDict = json.load(jsonFile)

  jsonObject = jsonDict["DefaultConfig"][0]
  objectString = json.dumps(jsonObject)
  database["Guild Config For " + str(guildID)] = objectString

def updateConfig(database, guildID, key, new):
  jsonObject = json.loads(database["Guild Config For " + str(guildID)])
  jsonObject[key] = new
  objectString = json.dumps(jsonObject)
  database["Guild Config For " + str(guildID)] = objectString
