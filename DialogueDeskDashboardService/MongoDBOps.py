# mongo db specific
import pymongo
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

# others
import re
import pandas as pd
from config import *
from datetime import date


# Create a new client and connect to the server
uri = f"mongodb+srv://einsteinmuna:{MONGO_DB_PASSWORD}@dialoguedesk.gb7wh.mongodb.net/?retryWrites=true&w=majority&appName=DialogueDesk"

# db and collection (sync)
sync_client = MongoClient(uri, server_api=ServerApi('1'))
DialogueDeskDB = sync_client.DialogueDeskNoSQLDb
DialogueDeskCollection = DialogueDeskDB["Meetings_Insights"]
# DialogueDeskMeetingsC = DialogueDeskDB["DialogueDeskComplaints"]

# db and collection (async)
async_client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
DialogueDeskDB = async_client.DialogueDeskNoSQLDb
DialogueDeskMeetingsC = DialogueDeskDB["DialogueDeskComplaints"]
# DialogueDeskMeetingsC = DialogueDeskDB["DialogueDeskComplaints"]


def upload_data(data: dict):
    """
    For uploading meeting insights. Input format ->
    {
        "Date": meeting_date,
        "meeting_id": f"Meeting - {meeting_time}", 
        "transcript": transcript, 
        "ai_summary": insights.get("Summary", "No summary available"),
        "key_points" : insights.get("key_points_discussed", []),
        "action_items" : insights.get("action_items", []) 
    }
    """
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


def search_by_date_and_id(date_id_tup: str) -> dict:
    """
    sample input:
        2025-01-23 | Meeting 3
        2025-01-23 Meeting 1

        No need for any fancy formatting as regex is used to pick the date and meeting id.

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

        date_pattern, meeting_id_pattern = r"\d{4}-\d{2}-\d{2}", r"Meeting - \d{2}:\d{2}"
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
        print(f"ERROR in Meetings Data retrieval: {e}")
        output = {
            "transcript" : "None available at the moment",
            "ai_summary" : "None available at the moment",
            "key_points" : [],
            "action_items" : [],
        }
        return output
    

async def create_complaints_dataframe():
    """
    Retrieves all complaints in chunks of 100, formats them to a DataFrame, and returns the DataFrame.
    """
    try:
        # Initialize an empty list to hold complaint data
        all_complaints = []

        # Cursor to fetch complaints in chunks of 100
        complaints_cursor = DialogueDeskMeetingsC.find()
        
        while True:
            # Fetch the next chunk of complaints
            complaints = await complaints_cursor.to_list(length=100)

            # Break the loop if there are no more complaints
            if not complaints:
                break

            # Extract relevant fields from the chunk and append them to all_complaints
            for complaint in complaints:
                all_complaints.append([
                    complaint.get("complaint_text", ""),
                    complaint.get("date", ""),
                    complaint.get("complaint_topic_1", ""),
                    complaint.get("complaint_topic_2", ""),
                    complaint.get("receive_update", ""),
                    complaint.get("status", ""),
                ])

        # Create DataFrame only if there are complaints
        if all_complaints:
            columns = ["complaint_text", "date", "topic_1", "topic_2", "update_preference", "complaint_status"]
            complaints_df = pd.DataFrame(all_complaints, columns=columns)
            return complaints_df
        else:
            print("No complaints found in the database... default df returned")
            
            columns = ["complaint_text", "date", "topic_1", "topic_2", "update_preference", "complaint_status"]
            default_values = ["No data available"] * len(columns)
            df_no_data = pd.DataFrame([default_values], columns=columns)
            return df_no_data

    except Exception as e:
        print(f"An error occurred while retrieving complaints: {str(e)}")
        columns = ["complaint_text", "date", "topic_1", "topic_2", "update_preference", "complaint_status"]
        default_values = ["No data available"] * len(columns)
        df_no_data = pd.DataFrame([default_values], columns=columns)
        return df_no_data


def get_todays_date(random):
    """
    Returns today's date in YYYY-MM-DD format.
    random is not useful... just put that there because langchain agent kept messing up the tool call.
    """
    today = date.today()
    return today.strftime("%Y-%m-%d")


# print(get_todays_date("age"))








# def create_complaints_dataframe():
#     """
#     Retrieves all complaints in chunks of 100, formats them to a DataFrame, and returns the DataFrame.
#     """
#     try:
#         # Initialize an empty list to hold complaint data
#         all_complaints = []

#         # Cursor to fetch complaints
#         complaints_cursor = DialogueDeskMeetingsC.find()

#         # Fetch complaints in chunks of 100
#         while True:
#             # Fetch the next chunk of complaints
#             complaints = list(complaints_cursor.clone().limit(100))  # Clone the cursor and apply limit

#             # Break the loop if there are no more complaints
#             if not complaints:
#                 break

#             # Extract relevant fields from the chunk and append them to all_complaints
#             for complaint in complaints:
#                 all_complaints.append([
#                     complaint.get("date", ""),
#                     complaint.get("complaint_text", ""),
#                     complaint.get("complaint_topic_1", ""),
#                     complaint.get("complaint_topic_2", ""),
#                     complaint.get("receive_update", ""),
#                     complaint.get("status", ""),
#                 ])

#         # Create DataFrame only if there are complaints
#         if all_complaints:
#             columns = ["date", "complaint_text", "topic_1", "topic_2", "update_preference", "complaint_status"]
#             complaints_df = pd.DataFrame(all_complaints, columns=columns)
#             return complaints_df
#         else:
#             print("No complaints found in the database... default df returned")

#             # Default DataFrame when no data is available
#             columns = ["date", "complaint_text", "topic_1", "topic_2", "update_preference", "complaint_status"]
#             default_values = ["No data available"] * len(columns)
#             df_no_data = pd.DataFrame([default_values], columns=columns)
#             return df_no_data

#     except Exception as e:
#         print(f"An error occurred while retrieving complaints: {str(e)}")

#         # Default DataFrame in case of an error
#         columns = ["date", "complaint_text", "topic_1", "topic_2", "update_preference", "complaint_status"]
#         default_values = ["No data available (exception occurred)"] * len(columns)
#         df_no_data = pd.DataFrame([default_values], columns=columns)
#         return df_no_data