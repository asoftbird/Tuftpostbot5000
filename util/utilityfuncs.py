import os
import sys
import json
import logging
import exceptions

from genericpath import exists
from datetime import datetime
from dotenv import load_dotenv

from .exceptions import FileNotEmpty

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
    timestampStr = dateTimeObj.strftime("%d%m%Y_%H-%M-%S")
    return(timestampStr)

# deprecated, here for compat
def writeToLog(message):
    with open(str(LOGFILE), "a") as log:
        log.write(getTime() + " " + str(message) + "\n")

def funcName(level):
    # get name of calling function
    return sys._getframe(level + 1).f_code.co_name

def getExceptionString(e):
    # return preformatted string to display exception source
    return (f"{type(e).__name__} at {funcName(1)}, line {e.__traceback__.tb_lineno} of {sys.argv[0]}: ")





# TODO: function for checking if log exists / create if not exists
# TODO: log file split after x lines 


# file helpers
def load_json(file):
    data = ""
    with open(file, "r") as jsonfile:
        data = json.load(jsonfile)
        return data



def createFile(fullpath):
    try:
        if exists(fullpath): 
            raise FileExistsError
        else:
            logging.info(f"Creating {fullpath}")
            with open(fullpath, "x") as newfile:
                newfile.write("\n")
        
    except FileExistsError as e:
        logging.info(getExceptionString(e) + f"File {fullpath} already exists.")
        pass

def deleteFile(fullpath):
    try:
        if not exists(fullpath):
            raise FileNotFoundError
        else:
            os.remove(fullpath)
            logging.info(f"Deleted file {fullpath}.")

    except FileNotFoundError as e:
        logging.info(getExceptionString(e) + f"File {fullpath} does not exist.")

def writeFirstLine(fullpath, text):
    try:
        if not exists(fullpath):
            raise FileNotFoundError
        elif getFileSize(fullpath) > 0:
            raise FileExistsError
        else:
            with open(fullpath, "x") as openfile:
                openfile.write(text)

    except FileNotFoundError as e:
        logging.info(getExceptionString(e) + f"File {fullpath} does not exist.") 
    
    except FileNotEmpty as e:
        logging.info(getExceptionString(e) + f"File {fullpath} already contains data.")





def getFileSize(fullpath):
    # Return file size in MB
    try:
        if exists(fullpath):
            return round(os.path.getsize(fullpath)/(1<<20), 4)
        else:
            raise FileNotFoundError
            
    except FileNotFoundError as e:
        logging.info(getExceptionString(e) + f"File {fullpath} does not exist.")
        return None


# createFile("asdf.txt")

# writeFirstLine("asdfs.txt", "some text")

# writeFirstLine("asdf.txt", "some text")

def errortime():
    print("error!")


def checkErrors(func):
    def handler(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except FileNotFoundError as e:
            logging.info(getExceptionString(e) + f"File {args[0]} does not exist.")
        except FileExistsError as e:
            logging.info(getExceptionString(e) + f"File {args[0]} already exists.")
        except FileNotEmpty as e:
            logging.info(getExceptionString(e) + f"File {args[0]} already contains data.")
    return handler

@checkErrors
def getFileSizeE(fullpath):
    # Return file size in MB
    if exists(fullpath):
        return round(os.path.getsize(fullpath)/(1<<20), 4)
    else:
        raise FileNotFoundError


getFileSizeE("asdssdfdsgdf.txt")











# def rotateLogFiles(log_directory, base_name, latest_log, maxsize):
#     # Generate new log file if current log file exceeds a certain size
#     try:
#         if exists(latest_log):
#             latest_size = getFileSize(latest_log)
#             if latest_size >= maxsize:
#                 # rename latest.log to base_name_[date-time].log, where date is sourced from first line of current log file
#                 # create new latest.log file
#                 # write current date-time to first line of new latest.log file

#         else:
#             logging.warning(f"Log file {latest_log} not found!")
#             raise FileNotFoundError


# tc = unittest.TestCase()
# tc.assertIsNotNone(a)