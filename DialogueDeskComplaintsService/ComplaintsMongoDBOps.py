# mongo db specific
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

# others
import json
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
        result = DialogueDeskCollection.insert_one(parsed_json)  # Synchronous insertion
        return result.inserted_id  # Return the inserted document ID
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None