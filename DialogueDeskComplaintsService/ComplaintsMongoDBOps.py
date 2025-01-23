# async mongo db operations  specific
import motor.motor_asyncio
from pymongo.server_api import ServerApi
from pymongo.errors import OperationFailure
from motor.motor_asyncio import AsyncIOMotorClient

# others
import json
from config import MONGO_DB_PASSWORD

# db and collection
uri = f"mongodb+srv://einsteinmuna:{MONGO_DB_PASSWORD}@dialoguedesk.gb7wh.mongodb.net/?retryWrites=true&w=majority&appName=DialogueDesk"
client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
DialogueDeskDB = client.DialogueDeskNoSQLDb
DialogueDeskCollection = DialogueDeskDB["DialogueDeskComplaints"]


async def lodge_complaint(data: dict):
    try:
        # str to json here
        parsed_json = json.loads(data)

        if not isinstance(parsed_json, dict):
            raise ValueError("The data must be a dictionary.")
        
        # Ensure that the required fields are in the input data
        required_fields = ["complaint_text", "complaint_topics", "receive_update", "status"]
        if not all(field in parsed_json for field in required_fields):
            print("Error: Missing required fields in the input data.")
            return None
        
        # Insert the complaint into the database
        result = await DialogueDeskCollection.insert_one(parsed_json)
        return result.inserted_id
    
    except OperationFailure:
        print("An authentication error was received. Please ensure the database user has the proper permissions for write operations.")
    except ValueError as ve:
        print(str(ve))
    except Exception as e:
        print(f"An error occurred: {str(e)}")