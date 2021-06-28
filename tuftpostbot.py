import os
import json
import random
import tweepy
import flickrapi
import wget
import shortuuid

from time import sleep
from dotenv import load_dotenv
from datetime import datetime
from PIL import Image
from urllib import request
from fastai.vision.all import *
from fastai.text.all import *
from fastai.collab import *
from fastai.tabular.all import *


load_dotenv()
# API auth keys
CONS_KEY=os.getenv('TWT_CONSUMER_APIKEY')
CONS_SEC=os.getenv('TWT_CONSUMER_APISECRET')
AUTH_ACC=os.getenv('TWT_AUTH_ACCESSTOKEN')
AUTH_SEC=os.getenv('TWT_AUTH_SECRET')
FLKR_KEY=os.getenv('FLICKR_KEY')
FLKR_SEC=os.getenv('FLICKR_SECRET')

# config
FETCH_COUNT = 25 #50
PAGE_RANGE = 79 #79
BLOCKLIST = ["61021753@N02", "93689361@N05"]
SAVED_IMAGES = "/tuftml"
FILE_PATH = os.getcwd() + SAVED_IMAGES
LOGFILE = "titpostbotlog.txt"
EXTRA_ARGS = 'url_o, owner_name, path_alias'
TAGS = 'tufted titmouse'
RESOLUTION = 1600 #pixels, width

# references
auth = tweepy.OAuthHandler(CONS_KEY, CONS_SEC)
auth.set_access_token(AUTH_ACC, AUTH_SEC)
api = tweepy.API(auth, wait_on_rate_limit=True)
flickr = flickrapi.FlickrAPI(FLKR_KEY, FLKR_SEC, format='parsed-json')

# try:
#     api.verify_credentials()
#     print("Authentication OK")
# except:
#     print("Error during authentication")

# utility functions
def getTime():
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("[%d-%m-%Y %H:%M:%S]")
    return(timestampStr)

def writeToLog(message):
    output = open(str(LOGFILE), "a")
    output.write(getTime() + " " + str(message) + "\n")
    output.close()

def deleteAllTempImages(folder_path):
    for file in os.scandir(folder_path):
        os.remove(file.path)

def deleteSingleImage(folder_path, filename):
    full_path = folder_path+"/"+filename
    #print(f"deleted {full_path} :D")
    os.remove(full_path)

def findStringInNestedList(search_list, search_string):
    for sublist in search_list:
        try:
            if search_string in sublist:
                return search_list.index(sublist), sublist.index(search_string)
        except TypeError:
            print("Index not found!")

# this needs to be up here because fastai is a dummy
def is_tufter(filename):
    return filename[0].isupper()

# always keep this below def is_tufter() to avoid bugs
learn = load_learner('tuftmodel_v8_10ep_lr0.001.pkl')

#main functions
def findBirdImage(search_tags, extra_arguments, image_fetch_count):
    page_number = random.randint(1, PAGE_RANGE)
    search_arguments = [extra_arguments]
    search_query = flickr.photos.search(tags=search_tags, extras=search_arguments, per_page=image_fetch_count, page=page_number)
    return search_query


# filter based on functionality; filtering on bird type comes later
def filterSearchResults(search_query):
    image_url_data = ""
    photo_id = ""
    photo_owner_id = ""
    photo_owner_name = ""
    rejected = 0
    b_pathalias = False
    b_returned_image = False

    for v in search_query["photos"]["photo"]:
        if "url_o" in v:
            image_url_data = v["url_o"]
            b_returned_image = True
            if "owner" in v:
                photo_owner_id = v["owner"]
                photo_id = v["id"]
            if "pathalias" in v:
                if v["pathalias"] != None:
                    photo_owner_name = v["pathalias"]
                    f_pathAlias = True
                else:
                    photo_owner_name = v["ownername"]
                    f_pathAlias = False
        else:
            rejected = rejected + 1

    if len(image_url_data) == 0:
        return ([], False)

    data_list_full = [image_url_data, photo_owner_name, photo_id, photo_owner_id]
    return(data_list_full, b_returned_image)


def collectInitialImageDataSet(count, max_requests):
    iterator = 0
    foundImages = 0
    result_data_set = []

    while foundImages < count:
        sleep(1)
        data_set, b_returned_image = filterSearchResults(findBirdImage(TAGS, EXTRA_ARGS, FETCH_COUNT))
        if b_returned_image == False:
            # no images found
            iterator += 1
        elif b_returned_image == True:
            # found image
            foundImages += 1
            print(f"Found {foundImages} images...")
            iterator += 1
            result_data_set.append(data_set)
        if iterator >= max_requests:
            break
    result_string = str(f"Found {count} images in {iterator}/{max_requests} attempts.")
    print(result_string)
    writeToLog(result_string)

    return result_data_set

def downloadImagesFromURL(data_set, destination_path):
    list_filenames = []

    if len(data_set) < 1:
        print("Dataset empty! AAAAAAAA")
        # TODO handle exception

    for i, url in enumerate(data_set):
        file_extension = str(url[0][-4:])
        file_name = url[2]
        file_name_full = file_name+file_extension
        dl_image = urllib.request.urlretrieve(url[0], filename=destination_path+"/"+file_name_full)
        list_filenames.append(file_name_full)
    return list_filenames

# resize before using ML inference; operates faster on smaller images (if images are larger than 1600px)
def resizeImages(list_filenames, filepath, target_path, width):
    for i, file in enumerate(list_filenames):
        full_path = filepath+"/"+file
        filename_no_extension = file[:-4]

        image = Image.open(full_path)
        width_percentage = (width/float(image.size[0]))
        height_size = int((float(image.size[1])*float(width_percentage)))
        image = image.resize((width, height_size), Image.ANTIALIAS)
        image.convert('RGB').save((target_path + "/" + "rs_" + filename_no_extension+".jpg"), format="JPEG")




def checkTufts(filepath, image_data_list):
    for file in os.listdir(filepath):
        img = PILImage.create(str(filepath)+"/"+str(file))
        is_tufter,_,probs = learn.predict(img)
        #print(f"Is {file} a tuftie? {is_tufter} ({probs[1].item():.6f})")
        #if is_tufter == "False":
        if probs[1].item() < 0.90:
            deleteSingleImage(filepath, file)
            image_id = file.replace("rs_", "").replace(".jpg", "")
            index_a, index_b = findStringInNestedList(image_data_list, image_id)
            del image_data_list[index_a]
        else:
            image_id = file.replace("rs_", "").replace(".jpg", "")
            index_a, index_b = findStringInNestedList(image_data_list, image_id)
            probability = '{:.6f}'.format(probs[1].item())
            image_data_list[index_a].append(probability)
            image_data_list[index_a].append(str(is_tufter))

    final_data_table = image_data_list
    return final_data_table


def pickBestTuftieFromResults(input_list):
    try:
        index = random.randint(0, len(input_list)-1)
        result_list = input_list[index]
        return result_list
    except:
        backup_tuft = ['http://example.com', 'tuftpostbot5000', 'backuptuft', '12345', '4325.000', 'YES']
        return backup_tuft


def postBirdToTwitter(picked_image):
    owner_name = picked_image[1]
    filename = picked_image[2]
    owner_id = picked_image[3]
    probability = picked_image[4]
    istuft = picked_image[5]
    media_id_list = []

    if owner_name == "tuftpostbot5000":
        # using fallback tufterino
        file_path = "backuptuft"
    else:
        file_path = "resized"

    image_name = "rs_"+filename+".jpg"
    full_path = file_path+"/"+image_name


    media_info = api.simple_upload(filename=full_path)
    media_id_list.append(media_info.media_id)

    status_text = (f"#Tuftpostbot Tuftie: {istuft}({probability}). Photo by {owner_name}")
    writeToLog(status_text)

    posted_status_info = api.update_status(status=status_text, media_ids=media_id_list)
    media_id_list.clear()

# TODO:
# keep files in /resized/ around so there's a supply of tufterinos available
# handle duplicates / post archive pic if bot can't find any image


# clear temp folders before loading new images
deleteAllTempImages("ids")
deleteAllTempImages("resized")

print("\n Looking for new tufties!\n")
writeToLog("Looking for tufties!")
initial_data_set  = (collectInitialImageDataSet(5, 40))
downloaded_filename_list = downloadImagesFromURL(initial_data_set, "ids")

resizeImages(downloaded_filename_list, "ids", "resized", RESOLUTION)

result_list = checkTufts("resized", initial_data_set)
print(result_list)

pick = pickBestTuftieFromResults(result_list)
print(f"Picked {pick} as #1 best tuftie of the year!")
writeToLog(pick)

postBirdToTwitter(pick)
