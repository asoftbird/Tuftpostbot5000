from os import getenv
from datetime import datetime
import json
from dotenv import load_dotenv

load_dotenv()

# load logfile locaiton
with open("config.json", "r") as configfile:
    LOGFILE = json.load(configfile)["config-base"]["LOGFILE"]

print(f"Using log \'{LOGFILE}\'.")

# Logging functions
def getTime():
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("[%d-%m-%Y %H:%M:%S]")
    return(timestampStr)

def writeToLog(message):
    with open(str(LOGFILE), "a") as log:
        log.write(getTime() + " " + str(message) + "\n")

def load_json(file):
    data = ""
    with open(file, "r") as jsonfile:
        data = json.load(jsonfile)
        return data

print(load_json("config.json")["config-main"]["DEFAULT_MSG_PREFIX"])

# TODO: function for checking if log exists / create if not exists
# TODO: log file split after x lines 
