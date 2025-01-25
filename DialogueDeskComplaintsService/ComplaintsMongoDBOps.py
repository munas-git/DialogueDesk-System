# mongo db specific
from bson.errors import InvalidId
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

# others
import json
from typing import Literal
from config import MONGO_DB_PASSWORD

# db and collection
uri = f"mongodb+srv://einsteinmuna:{MONGO_DB_PASSWORD}@dialoguedesk.gb7wh.mongodb.net/?retryWrites=true&w=majority&appName=DialogueDesk"
client = MongoClient(uri, server_api=ServerApi('1'))
DialogueDeskDB = client.DialogueDeskNoSQLDb
DialogueDeskCollection = DialogueDeskDB["DialogueDeskComplaints"]


def lodge_complaint(data: dict):
    """
    Input:
        Json style string with keys {"complaint_text", "complaint_topic_1", "complaint_topic_2", "receive_update", "status"}
    """
    try:
        # Parse and validate the input data
        parsed_json = json.loads(data)
        if not isinstance(parsed_json, dict):
            raise ValueError("The data must be a dictionary.")
        
        required_fields = ["complaint_text", "complaint_topic_1", "complaint_topic_2", "receive_update", "status"]
        if not all(field in parsed_json for field in required_fields):
            print("Error: Missing required fields in the input data.")
            return None
        
        # Insert the complaint into the database
        result = DialogueDeskCollection.insert_one(parsed_json)
        return result.inserted_id
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
    

def db_get_complaint_status(report_id: str):
    try:
        object_id = ObjectId(str(report_id))

        # Query the database for the complaint
        result = DialogueDeskCollection.find_one({"_id": object_id})
        
        if result:
            return result.get("status")
        else:
            return "Complaint not found."
    except InvalidId:
        print("REPORT ID ENTERED ISSSSS",report_id)
        return "Invalid complaint ID format."
    except PyMongoError as e:
        return f"Database error: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"


def change_notification_preference(report_id: str, new_status: Literal["yes", "no"]):
    try:
        object_id = ObjectId(report_id)

        result = DialogueDeskCollection.update_one(
            {"_id": object_id},
            {"$set": {"receive_update": new_status}}
        )
        ropic = DialogueDeskCollection.find_one({"_id": object_id})["complaint_topic_1"]
    
        if result.matched_count > 0:
            print(f"Document updated successfully. Modified count: {result.modified_count}")
            return new_status, ropic
        else:
            print("No document found with that ID.")
            "complaint not found, and status not changed"
    except Exception as e:
        print("Error in notification status update:", e)
        "complaint not found, and status not changed"



# def update_complaint_status(report_id: str, new_status: Literal["pending", "resolved"]):
#     try:
#         object_id = ObjectId(report_id)

#         result = DialogueDeskCollection.update_one(
#             {"_id": object_id},
#             {"$set": {"status": new_status}}
#         )

#         if result.matched_count > 0:
#             print(f"Document updated successfully. Modified count: {result.modified_count}")
#             return f"new status {new_status}"
#         else:
#             print("No document found with that ID.")
#             return "complaint not found, and status not changed"
#     except Exception as e:
#         print("Error:", e)
#         return "complaint not found, and status not changed"