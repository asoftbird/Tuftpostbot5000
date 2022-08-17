from dataclasses import dataclass
import os
import sys
import json
import logging

from genericpath import exists
from datetime import datetime
from dotenv import load_dotenv
from exceptions import *

load_dotenv()

# load logfile location
with open("config.json", "r") as configfile:
    LOGFILE = json.load(configfile)["config-base"]["LOGFILE"]

logging.basicConfig(filename=LOGFILE, 
    encoding='utf-8', 
    level=logging.DEBUG, 
    format='%(asctime)s %(message)s',
    datefmt='[%a %d-%m-%y %H:%M:%S]'
    )


####################
# Helper functions #
####################

# Logging functions
def getTime():
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%a_%d%m%Y_%H-%M-%S")
    return(timestampStr)

# deprecated, here for compat
def writeToLog(message):
    with open(str(LOGFILE), "a") as log:
        log.write(getTime() + " " + str(message) + "\n")


################################
# Exception handler  functions #
################################

def funcName(level):
    # get name of calling function
    return sys._getframe(level + 1).f_code.co_name

def getExceptionString(e, func):
    # return preformatted string to display exception source
    return (f"{type(e).__name__} at {func.__name__} in {sys.argv[0]}: ")

# Exception handler decorator
def checkErrors(func):
    def handler(*args, **kwargs):
        try:
            a = func(*args, **kwargs)
            return a
        except FileNotFoundError as e:
            logging.info(getExceptionString(e, func) + f"File {args[0]} does not exist.")
        except FileExistsError as e:
            logging.info(getExceptionString(e, func) + f"File {args[0]} already exists.")
        except FileNotEmpty as e:
            logging.info(getExceptionString(e, func) + f"File {args[0]} already contains data.")
        except TypeError as e:
            logging.error(getExceptionString(e, func) + f"TypeError at {args[0]}")
    return handler


#########################
# File helper functions #
#########################

# TODO: function for checking if log exists / create if not exists
# TODO: log file split after x lines 

def load_json(file):
    data = ""
    with open(file, "r") as jsonfile:
        data = json.load(jsonfile)
        return data

@checkErrors
def createFile(fullpath):
    if exists(fullpath): 
        raise FileExistsError
    else:
        logging.info(f"Creating {fullpath}")
        with open(fullpath, "x") as newfile:
            newfile.write("\n")

@checkErrors
def deleteFile(fullpath):
    if not exists(fullpath):
        raise FileNotFoundError
    else:
        os.remove(fullpath)
        logging.info(f"Deleted file {fullpath}.")

@checkErrors
def writeFirstLine(fullpath, text):
    if not exists(fullpath):
        raise FileNotFoundError
    elif getFileSizeB(fullpath) <= 1:
        raise FileNotEmpty
    else:
        with open(fullpath, "w") as openfile:
            openfile.write(text)

@checkErrors
def getFileSize(fullpath):
    # Return file size in MB
    if exists(fullpath):
        return round(os.path.getsize(fullpath)/(1<<20), 4)
    else:
        raise FileNotFoundError

@checkErrors
def getFileSizeB(fullpath):
    # Return file size in B
    if exists(fullpath):
        return os.path.getsize(fullpath)
    else:
        raise FileNotFoundError


createFile("asdf.txt")














def rotateLogFiles(log_directory, base_name, latest_log, maxsize):
    # Generate new log file if current log file exceeds a certain size
        if exists(latest_log):
            latest_size = getFileSize(latest_log)
            if latest_size >= maxsize:
                # rename latest.log to base_name_[date-time].log, where date is sourced from first line of current log file
                # create new latest.log file
                # write current date-time to first line of new latest.log file
                writeFirstLine("asdf.txt", getTime()+"\n")

        else:
            logging.warning(f"Log file {latest_log} not found!")
            raise FileNotFoundError


# tc = unittest.TestCase()
# tc.assertIsNotNone(a)