import os
import json
import random
import tweepy
import flickrapi
import wget

from time import sleep
from dotenv import load_dotenv
from datetime import datetime
from PIL import Image

load_dotenv()
# API auth keys
CONS_KEY=os.getenv('TWT_CONSUMER_APIKEY')
CONS_SEC=os.getenv('TWT_CONSUMER_APISECRET')
AUTH_ACC=os.getenv('TWT_AUTH_ACCESSTOKEN')
AUTH_SEC=os.getenv('TWT_AUTH_SECRET')
FLKR_KEY=os.getenv('FLICKR_KEY')
FLKR_SEC=os.getenv('FLICKR_SECRET')

# config
FETCH_COUNT = 100
PAGE_RANGE = 30 #requests are limited to ~4000 images, beyond that repeats will occur
BLOCKLIST = ["61021753@N02", "93689361@N05"]
SAVED_IMAGES = "/img"
FILEPATH = os.getcwd() + SAVED_IMAGES
LOGFILE = "titpostbotlog.txt"
SEARCH_TAGS = 'tufted titmouse' #one string, comma-separated tags

# references
auth = tweepy.OAuthHandler(CONS_KEY, CONS_SEC)
auth.set_access_token(AUTH_ACC, AUTH_SEC)
api = tweepy.API(auth, wait_on_rate_limit=True)
flickr = flickrapi.FlickrAPI(FLKR_KEY, FLKR_SEC, format='parsed-json')

try:
    api.verify_credentials()
    print("Authentication OK")
except:
    print("Error during authentication")

# simple_upload(filename, *, file, media_category, additional_owners)

# - retrieve image from flickr once an hour
# - download file temporarily
# - upload file to twitter
# - delete temp file


# utility functions
def getTime():
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("[%d-%m-%Y %H:%M:%S]")
    return(timestampStr)

def writeToLog(message):
    output = open(str(LOGFILE), "a")
    output.write(getTime() + " " + message + "\n")
    output.close()

# main functions
def findBirdImageUrl(i_COUNT):
    pageNum = random.randint(1, PAGE_RANGE)
    argExtras = 'url_o, owner_name, path_alias'

    searchQuery = flickr.photos.search(tags=SEARCH_TAGS, extras=argExtras, per_page=i_COUNT, page = pageNum)

    blocked = 0
    denied = 0
    data = []
    photoOwner = []
    photoID = []
    photoOwnerName = []
    f_pathAlias = False #for logging purposes

    data.clear()
    photoOwner.clear()
    photoID.clear()
    photoOwnerName.clear()

    for v in searchQuery["photos"]["photo"]:
        if str(v["owner"]) not in BLOCKLIST:
            if "url_o" in v:
                data.append(v["url_o"])
                if "owner" in v:
                    photoOwner.append(v["owner"])
                    photoID.append(v["id"])
                if "pathalias" in v:
                    if v["pathalias"] != None:
                        photoOwnerName.append(v["pathalias"])
                        f_pathAlias = True
                    else:
                        photoOwnerName.append(v["ownername"])
                        f_pathAlias = False

            else: denied = denied + 1
        else:
            blocked = blocked + 1

    # data list can be shorter than input list, base random selected int on culled data list
    if len(data) > 0:
        selectedIndex = random.randint(1, len(data))-1
    else:
        selectedIndex = 0

    writeToLog("Got " + str(i_COUNT) + " bird pics of which " + str(len(data)) + " valid.")
    writeToLog("Denied " + str(denied) + " images and blocked " + str(blocked) + " images.")
    if f_pathAlias == True:
        writeToLog("Sent image ID " + str(photoID[selectedIndex]) + " by user ID " + str(photoOwner[selectedIndex]) + " aka (PA) " + str(photoOwnerName[selectedIndex]) + ".")
    else:
        writeToLog("Sent image ID " + str(photoID[selectedIndex]) + " by user ID " + str(photoOwner[selectedIndex]) + " aka (NAME) " + str(photoOwnerName[selectedIndex]) + ".")
    writeToLog("Sent URL " + str(data[selectedIndex]))

    print(getTime() + " Got " + str(i_COUNT) + " bird pics of which " + str(len(data)) + " valid.")
    print(getTime() + " Denied " + str(denied) + " images and blocked " + str(blocked) + " images.")
    print(getTime() + " Sent image ID " + str(photoID[selectedIndex]) + " by user ID " + str(photoOwner[selectedIndex]) + " aka " + str(photoOwnerName[selectedIndex]) + ".")

    return(data[selectedIndex], photoOwnerName[selectedIndex])

def resizeImage(path, name, width):

    img = Image.open(path)
    wpercent = (width/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((width, hsize), Image.ANTIALIAS)
    img.save("img/" + "rs_" +name)
    img.close()
    os.remove(str(str(FILEPATH)+"/"+str(name)))

def cleanUpImages(name):
    os.remove(str(FILEPATH)+"/"+str(name))


def postBirdToTwitter(statusText):
    mediaIDList = []

    birdImageResult = findBirdImageUrl(FETCH_COUNT)
    imageURL = birdImageResult[0]
    ownerName = birdImageResult[1]

    fullImagePath = wget.download(imageURL, out=FILEPATH)
    print("") #this is here because wget is dumb

    tempImageName = fullImagePath.replace(str(FILEPATH)+"/", '')
    debugImageName = str("rs_"+tempImageName)

    resizeImage(fullImagePath, tempImageName, 1600)
    media_info = api.simple_upload(filename=str("img/"+"rs_"+tempImageName))
    mediaIDList.append(media_info.media_id)

    fStatusText = statusText + " (by " + str(ownerName) + " on flickr)"
    print(fStatusText)
    postedStatusInfo = api.update_status(status=fStatusText, media_ids=mediaIDList)
    writeToLog("Posted image ID " + debugImageName + " to Twitter at " + str(postedStatusInfo.created_at) + " at http://https://twitter.com/asoftbird/status/" + str(postedStatusInfo.id))

    mediaIDList.clear()
    return debugImageName


writeToLog("========= Starting image upload ========= ")

cleanUpImages(postBirdToTwitter("#Tuftpostbot"))

