# async mongo db operations  specific
# import motor.motor_asyncio
from pymongo.server_api import ServerApi
from motor.motor_asyncio import AsyncIOMotorClient

# others
import json
# import asyncio
import pandas as pd
from datetime import date
from config import MONGO_DB_PASSWORD

# db and collection
uri = f"mongodb+srv://einsteinmuna:{MONGO_DB_PASSWORD}@dialoguedesk.gb7wh.mongodb.net/?retryWrites=true&w=majority&appName=DialogueDesk"

client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
DialogueDeskDB = client.DialogueDeskNoSQLDb
DialogueDeskCollection = DialogueDeskDB["DialogueDeskComplaints"]


async def lodge_complaint(data: dict):
    """
    Input:
        Json style string with keys {complaint_text", "complaint_topic_1", "complaint_topic_2", "receive_update", "status}
    """
    try:
        parsed_json = json.loads(data)
        if not isinstance(parsed_json, dict):
            raise ValueError("The data must be a dictionary.")
        
        required_fields = ["complaint_text", "complaint_topic_1", "complaint_topic_2", "receive_update", "status"]
        if not all(field in parsed_json for field in required_fields):
            print("Error: Missing required fields in the input data.")
            return None
        
        # Insert the complaint into the database
        result = await DialogueDeskCollection.insert_one(parsed_json)
        return result.inserted_id
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")



# async def main():
#     all_complaints = await create_complaints_dataframe()
#     if all_complaints is not None:
#         print(f"Retrieved {len(all_complaints)} complaints:")
#         for complaint in all_complaints:
#             print(complaint)
#     else:
#         print("empty complaints")

# asyncio.run(main())


# async def close_client():
#     client.close()
