import os
from datetime import datetime
from .defaults import LOGFILE_DEFAULT, REGISTRY_DEFAULT

# utility functions
def getTime():
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("[%d-%m-%Y %H:%M:%S]")
    return(timestampStr)

def writeToLog(message, target_file=LOGFILE_DEFAULT):
    # TODO: implement proper logging

    with open(target_file, "a") as output:
        output.write(getTime() + " " + str(message) + "\n")

def deleteAllTempImages(folder_path):
    for file in os.scandir(folder_path):
        os.remove(file.path)

def deleteSingleImage(folder_path, filename):
    full_path = folder_path+"/"+filename
    os.remove(full_path)

def findStringInNestedList(search_list, search_string):
    for sublist in search_list:
        try:
            if search_string in sublist:
                return search_list.index(sublist), sublist.index(search_string)
        except TypeError:
            print("Index not found!")

# check if image exists in registry; returns True if already exists.
def checkImageIDInRegistry(string, target_file=REGISTRY_DEFAULT):
    try:
        with open(target_file, "r") as registry:
            return True if string in set(registry.read().split('\n')) else False

    except FileNotFoundError:
        print(f"File not found. Creating {target_file}")
        writeToLog("checkImageIDInRegistry: Registry file not found. Creating...")
        newfile = open(target_file, "x")
        newfile.close()
        return False

def writeImageIDToRegistry(string, target_file=REGISTRY_DEFAULT):
    try:
        if checkImageIDInRegistry(string) == False:
            with open(target_file, "a") as registry:
                registry.write(string+"\n")
                print(f"Wrote {string} to file")
                writeToLog("writeImageIDToRegistry: Wrote string " + string + " to registry.")
        else:
            print(f"Cannot write {string} to registry: already exists")

    except FileNotFoundError:
            print(f"File {target_file} not found. Creating and appending image ID.")
            writeToLog("writeImageIDToRegistry: Registry file not found. Creating...")
            with open(target_file, "a") as newregistry:
                newregistry.write(string)
                print(f"Wrote {string} to new file")