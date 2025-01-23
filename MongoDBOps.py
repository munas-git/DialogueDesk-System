# mongo db specific
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# others
import re
from config import *


# Create a new client and connect to the server
uri = f"mongodb+srv://einsteinmuna:{MONGO_DB_PASSWORD}@dialoguedesk.gb7wh.mongodb.net/?retryWrites=true&w=majority&appName=DialogueDesk"
client = MongoClient(uri, server_api=ServerApi('1'))

# db and collection
DialogueDeskDB = client.DialogueDeskNoSQLDb
DialogueDeskCollection = DialogueDeskDB["Meetings_Insights"]


def upload_data(data: dict):
    try:
        result = DialogueDeskCollection.insert_one(data)
    except pymongo.errors.OperationFailure:
        print("An authentication error was received. Are you sure your database user is authorized to perform write operations?")


def meetings_metadata_by_date(date: str) -> dict:
    """Just returns number of meetings and meetings ids
    Output:
        {"no_of_meetings": *, "meeting_ids": [...]}
    """
    try:
        # formatting date to combat agent issue of passing date the wrong way.
        result = DialogueDeskCollection.find({"Date" : date.strip("'").strip('"')})
        meeting_ids = [content["meeting_id"] for content in list(result)]

        output = {
            "no_of_meetings" : len(meeting_ids),
            "meeting_ids" : meeting_ids,
        }
        return output

    except Exception as e:
        print(f"ERROR Retrieving date: {e}")


def search_by_date_and_id(date_id_tup: tuple) -> dict:
    """
    Sample output...
    {
        "transcript" : "None available at the moment",
        "ai_summary" : "None available at the moment",
        "key_points" : [],
        "action_items" : [],
    }
    """
    try:
        # I think langchain agent is passing the input as string instead of actual tuple
        # using regex to extract date and id from ... tried wraping with tuple but didnt work hence this hack (at least for now)

        date_pattern, meeting_id_pattern = r"\d{4}-\d{2}-\d{2}", r"Meeting\s\d+"
        ################# incase of errors thrown because of invalid meeting info, check back here #############
        date, meeting_id = re.findall(date_pattern, date_id_tup)[0], re.findall(meeting_id_pattern, date_id_tup)[0]

        result = DialogueDeskCollection.find_one({"Date" : date, "meeting_id" : meeting_id})

        output = {
            "transcript" : result["transcript"],
            "ai_summary" : result["ai_summary"],
            "key_points" : result["key_points"],
            "action_items" : result["action_items"],
        }
        return output

    except Exception as e:
        print(f"ERROR: {e}")
        
        output = {
            "transcript" : "None available at the moment",
            "ai_summary" : "None available at the moment",
            "key_points" : [],
            "action_items" : [],
        }
        return 
    

# search_by_date_and_id("2025-01-22, Meeting 1")
# print(DialogueDeskCollection.find_one({"Date" : "2025-01-15", "meeting_id" : "Meeting 1"}))