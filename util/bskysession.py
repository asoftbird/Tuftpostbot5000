import os
import sys
from dotenv import load_dotenv
from atproto import Client
import time
import json

load_dotenv()
username = str(os.getenv('BSKY_UNAME'))
password = str(os.getenv('BSKY_PASS'))

session_file = "session.json"
time_valid = 7200
# that is 2 hours
# in seconds! default is 30 days

def getCurrentTime():
    return int(time.time())

def getExpiryTime(creation_time):
    # 30 days; atproto protocol session token has 2month validity
    return creation_time + (time_valid)

def checkSessionValidity():
    current_time = getCurrentTime()
    try:
        with open(session_file, 'r') as file:
            data = json.load(file)
        expiry_time = data['expiry']
        created_time = data['created']

        if expiry_time < current_time:
            print(f"Session valid until {expiry_time} exceeds current time {current_time}. Generating new session token.")
            createNewSession()
        else:
            print(f"Session token valid until {expiry_time} ({(expiry_time - current_time) / 3600} hours remaining)")
    except json.JSONDecodeError as e:
        print(f"{e}: JSON file invalid; file likely empty. Generating new session token.")
        expiry_time = createNewSession()
        print(f"Created new session, valid until {expiry_time} ({time_valid} seconds)")

def getSessionString():
    try:
        with open(session_file, 'r') as file:
            data = json.load(file)
        return data["session"]
    except json.JSONDecodeError as e:
        print(f"{e}")
        return None

def createNewSession():
    try:
        client = Client()
        client.login(username, password)
    except Exception as e:
        sys.exit(f"Bsky login failed: {e}")

    session_string = client.export_session_string()
    current_time = getCurrentTime()
    expiry_time = getExpiryTime(current_time)
    data = {
    "created": current_time,
    "expiry": expiry_time,
    "session": session_string
    }

    with open(session_file, 'w') as file:
        json.dump(data, file)

    return expiry_time


if __name__ == "__main__":
    print("Checking session validity..")
    checkSessionValidity()

