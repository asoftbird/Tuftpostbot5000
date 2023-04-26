import os
import sys
import json
import random
import tweepy
import flickrapi
import pathlib

from time import sleep
from dotenv import load_dotenv
from PIL import Image
from PIL import ImageOps
from fastai.vision.all import *
from fastai.text.all import *
from fastai.collab import *
from fastai.tabular.all import *
from discord_webhook import DiscordWebhook
from cohost.models.user import User
from cohost.models.block import MarkdownBlock



# linux / windows compatibility
base_posix_path = pathlib.PosixPath
if sys.platform.startswith("linux"):
    pass
elif sys.platform.startswith("win32"):
    pathlib.PosixPath = pathlib.WindowsPath

load_dotenv()
# API auth keys
CONS_KEY=os.getenv('TWT_CONSUMER_APIKEY')
CONS_SEC=os.getenv('TWT_CONSUMER_APISECRET')
AUTH_ACC=os.getenv('TWT_AUTH_ACCESSTOKEN')
AUTH_SEC=os.getenv('TWT_AUTH_SECRET')
FLKR_KEY=os.getenv('FLICKR_KEY')
FLKR_SEC=os.getenv('FLICKR_SECRET')
WEBHOOK_URL=os.getenv('WEBHOOK_URL')

# cohost env vars
CH_UNAME=os.getenv('COHO_UNAME')
CH_PW=os.getenv('COHO_PW')
CH_PAGE=os.getenv('COHO_PAGE')

# init
istuft = 0
probability = 0
owner_name = 0
backup_used_flag = False

# config
CONFIDENCE_THRESHOLD = 0.50
ATTEMPTS = 50
FETCH_COUNT = 15
PAGE_RANGE = 256
BLOCKLIST = ["61021753@N02", "101072775@N04", "120795404@N04"]
EXTRA_ARGS = 'url_o, owner_name, path_alias'
TAGS = 'tufted titmouse'
RESOLUTION = 1600 # (width)
DEFAULTMSG = (f"#Tuftpostbot Tuftie: {istuft}({probability}). Photo by {owner_name}")
ENABLE_WEBHOOK = True
ENABLE_COHOST = True


# paths
import util
util.setLogfile("tuftlog.log")
util.setRegistryFile("registry.txt")
from util.helpers import *

BACKUP_TUFT_DIR = "fallbacktuft"
BACKUP_METAFILE = "fallbackmeta.json"
IMAGE_STORE_DIR = "imagestore"
IMAGE_DOWNLOAD_DIR = "downloads"

# references
auth = tweepy.OAuthHandler(CONS_KEY, CONS_SEC)
auth.set_access_token(AUTH_ACC, AUTH_SEC)
api = tweepy.API(auth, wait_on_rate_limit=True)
flickr = flickrapi.FlickrAPI(FLKR_KEY, FLKR_SEC, format='parsed-json')

try:
    api.verify_credentials()
    print("Authentication OK")
except Exception as e:
    print(f"Error during authentication: {e}")



# TODO: check if required directories exist, if not, create them

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
        temp_image_id = v["id"]
        if not checkImageIDInRegistry(v["id"]):
            if not v["owner"] in BLOCKLIST:
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
                    b_returned_image = False
            else:
                print(f"Blocked image from {v['owner']}")
                rejected = rejected + 1
                b_returned_image = False
        else:
            print(f"ImageID {temp_image_id} already posted. Ignoring.")
            util.helpers.writeToLog("ImageID " + temp_image_id + " already posted. Ignoring.")
            b_returned_image = False

    if len(image_url_data) == 0:
        return ([], False)

    data_list_full = [image_url_data, photo_owner_name, photo_id, photo_owner_id]
    return(data_list_full, b_returned_image)


def asdf(metadata_list, filename):
    # take a list of data (image_url, ownername, photoid, ownerid, confidence, tuftness)
    # along with a filename
    # create a metadata.json file containing this data;
    # format:
    #     "UUID": {
    #         "url": "https://titmou.se/tuft.gif",
    #         "owner": "AAAAAA",
    #         "photo-id": 13245,
    #         "filename": "a",
    #         "owner-id": "5000",
    #         "confidence": "A",
    #         "istuft": "AAAAAAAAAAAAA"
    #     }
    # data will not be modified during runtime (ie. no "is posted?" flag)
    # does require duplicate checking though.
    # use checkImageIDInRegistry() for this?
    



    pass


def collectInitialImageDataSet(count, max_requests):
    iterator = 0
    foundImages = 0
    result_data_set = []

    while foundImages < count:
        sleep(1)
        data_set, b_returned_image = filterSearchResults(findBirdImage(TAGS, EXTRA_ARGS, FETCH_COUNT))
        if b_returned_image == False:
            iterator += 1
        elif b_returned_image == True:
            foundImages += 1
            print(f"Found {foundImages} images...")
            util.helpers.writeToLog(f"Found {foundImages} images...")
            iterator += 1
            result_data_set.append(data_set)
        if iterator >= max_requests:
            break
    result_string = str(f"Found {count} images in {iterator}/{max_requests} attempts.")
    print(result_string)
    util.helpers.writeToLog(result_string)

    return result_data_set

def downloadImagesFromURL(data_set, destination_path):
    list_filenames = []

    if len(data_set) < 1:
        print("Dataset empty! AAAAAAAA")
        util.helpers.writeToLog("dataset empty! AAAAAAA")
        # TODO handle exception

    for _, url in enumerate(data_set):
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
        image = ImageOps.exif_transpose(image) # if image is rotated; get correct rotation from EXIF metadata; if data is not present, just get a copy of 'image'
        width_percentage = (width/float(image.size[0]))
        height_size = int((float(image.size[1])*float(width_percentage)))
        image = image.resize((width, height_size), Image.ANTIALIAS)
        image.convert('RGB').save((target_path + "/" + "rs_" + filename_no_extension+".jpg"), format="JPEG")


def checkTufts(filepath, image_data_list):
    for file in os.listdir(filepath):
        img = PILImage.create(str(filepath)+"/"+str(file))
        is_tufter,_,probs = learn.predict(img)

        if probs[1].item() < CONFIDENCE_THRESHOLD:
            util.helpers.writeToLog(f"{file} rejected, {probs[1].item()}")
            util.helpers.deleteSingleImage(filepath, file)
            image_id = file.replace("rs_", "").replace(".jpg", "")
            index_a, index_b = util.helpers.findStringInNestedList(image_data_list, image_id)
            probability = '{:.4f}'.format(probs[1].item())
            image_data_list[index_a].append(probability)
            image_data_list[index_a].append(str(is_tufter))
            del image_data_list[index_a]
        else:
            util.helpers.writeToLog(f"{file} accepted, {probs[1].item()}")
            image_id = file.replace("rs_", "").replace(".jpg", "")
            index_a, index_b = util.helpers.findStringInNestedList(image_data_list, image_id)
            probability = '{:.4f}'.format(probs[1].item())
            image_data_list[index_a].append(probability)
            image_data_list[index_a].append(str(is_tufter))
    if len(image_data_list) == 0:
        util.helpers.writeToLog("CheckTufts: dataset empty!")
        print("CheckTufts: dataset empty!")

    final_data_table = image_data_list
    return final_data_table


def pickBackupTuftie():
    # select one of the entries in the metadata file at random
    with open(BACKUP_METAFILE) as file:
        data = json.load(file)
        
    keys = list(data)
    index = random.randint(0, len(data)-1)
    result_key = keys[index]
    result_data = data[result_key]

    # construct data table
    # format: ['url', 'owner', 'filename', 'owner-id', 'probability', 'istuft true/false']
    fallbackDataTable = list(result_data.values())
    print(fallbackDataTable)
    
    return fallbackDataTable



def pickBestTuftieFromResults(input_list, b_writeRegistry):
    util.helpers.writeToLog(f"input list length: {len(input_list)}. list: {input_list}")
    print(f"input list length: {len(input_list)}.")
    try:
        index = random.randint(0, len(input_list)-1)
        result_list = input_list[index]
        picked_image_id = input_list[index][2]
        print(f"index: {index}. results: {result_list}. ID: {picked_image_id}")
        util.helpers.writeToLog(f"index: {index}. results: {result_list}. ID: {picked_image_id}")
        if b_writeRegistry == True:
            util.helpers.writeImageIDToRegistry(picked_image_id)
        test_value = result_list[4]
        print(test_value)
        print(f"result_list: {result_list}")
        util.helpers.writeToLog(f"result list: {result_list}")
        return result_list
    except Exception as e:
        print(f"Exception {type(e).__name__} occurred in pickBestTuftieFromResults: {repr(e)}")
        util.helpers.writeToLog(f"Exception {type(e).__name__} occurred in pickBestTuftieFromResults: {repr(e)}")
        backup_used_flag = True
        backup_tuft = pickBackupTuftie()
        return backup_tuft


def postBirdToTwitter(picked_image, message="default", b_should_post=True):
    owner_name = picked_image[1]
    filename = picked_image[2]
    owner_id = picked_image[3]
    
    istuft = picked_image[5]
    media_id_list = []
    webhook_content = picked_image[0]

    try:
        probability = picked_image[4]
    except IndexError:
        print("Can't find probability somehow, using fallback data")
        owner_name = "tuftpostbot5000"
        filename = "backuptuft"
        probability = "OVER 9000"
        istuft = "YEEHAW"

    if backup_used_flag == True:
        print("WARNING: BACKUP IMAGE USED.")
        util.helpers.writeToLog("WARNING: BACKUP IMAGE USED.")
        file_path = "fallbacktuft"
    else:
        file_path = IMAGE_STORE_DIR

    image_name = "rs_"+filename+".jpg"
    full_path = file_path+"/"+image_name


    if message == "default":
        status_text = (f"#Tuftpostbot Tuftie: {istuft}({probability}). Photo by {owner_name}")

    else:
        status_text = (f"#Tuftpostbot {message}. Tuftie: {istuft}({probability}). Photo by {owner_name}")

    if b_should_post:
        #send to twitter
        media_info = api.simple_upload(filename=full_path)
        media_id_list.append(media_info.media_id)
        posted_status_info = api.update_status(status=status_text, media_ids=media_id_list)
        media_id_list.clear()
        print(f"Sent {status_text} to Twitter!")
        util.helpers.writeToLog(f"Sent {status_text} to Twitter!")

        media_url = posted_status_info.entities["media"][0]["media_url"]
        tweet_id = str(posted_status_info.id)
        tweet_url = "https://vxtwitter.com/asoftbird/status/"+tweet_id

        if ENABLE_WEBHOOK:
            #send to discord webhook
            discord_text = tweet_url
            webhook = DiscordWebhook(url=WEBHOOK_URL, content=discord_text)
            response = webhook.execute()
            print(f"Sent {discord_text} to Discord!")
            util.helpers.writeToLog(f"Sent {discord_text} to Discord!")

        if ENABLE_COHOST:
            #send to cohost
            user = User.login(CH_UNAME, CH_PW)
            project = user.getProject(CH_PAGE)
            newpost = project.post(status_text, blocks=[MarkdownBlock(f"![]({media_url})")], tags=['tuftpostbot'])
            print(f"Sent tweet to Cohost as well (hopefully)!")
            util.helpers.writeToLog(f"Sent tweet to Cohost as well (hopefully)!")

    else:
        print(f"Did not send to twitter/dc: NOPOST flag used. Text: {status_text}")
        util.helpers.writeToLog(f"Did not send to twitter/dc: NOPOST flag used. Text: {status_text}")

# TODO:
# keep files in /resized/ around so there's a supply of tufterinos available


# clear temp folders before loading new images

util.helpers.deleteAllTempImages(IMAGE_STORE_DIR)

if "NOPOST" in sys.argv:
    b_should_post = False
    b_writeRegistry = False
    message = "default"

else:
    b_should_post = True
    b_writeRegistry = True
    if len(sys.argv) <=1:
        print("starting without arguments")
        util.helpers.writeToLog("starting without arguments")
        message = "default"
    else:
        message = str(sys.argv[1])
        print(f"Using custom message '{message}'")
        util.helpers.writeToLog(f"Using custom message '{message}'")

chance = random.randint(0, 500)

print(f"\n Looking for new tufties! Rolled {chance}\n")
util.helpers.writeToLog(f"Looking for tufties! Rolled {chance}")

if chance != 42: 
    initial_data_set  = (collectInitialImageDataSet(5, ATTEMPTS))
    downloaded_filename_list = downloadImagesFromURL(initial_data_set, IMAGE_DOWNLOAD_DIR)

    resizeImages(downloaded_filename_list, IMAGE_DOWNLOAD_DIR, IMAGE_STORE_DIR, RESOLUTION)

    result_list = checkTufts(IMAGE_STORE_DIR, initial_data_set)

    pick = pickBestTuftieFromResults(result_list, b_writeRegistry)
else:
    print("\n Rolled a 42! Posting shitpost tuftie!\n")
    util.helpers.writeToLog("Rolled a 42! Posting shitpost tuftie!")
    # we do a lil titposting 
    pick = pickBackupTuftie()


print(f"Picked {pick} as #1 best tuftie of the year!")
util.helpers.writeToLog(pick)

postBirdToTwitter(pick, message, b_should_post)
util.helpers.deleteAllTempImages(IMAGE_DOWNLOAD_DIR)
