# langchain related
from langchain_openai import ChatOpenAI


# db ops related
from ComplaintsMongoDBOps import *

# others
import json
from config import OPEN_AI_KEY


class DialogueDeskAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            max_tokens=800,
            api_key=OPEN_AI_KEY
        )


    def classify_intent(self, input_string: str):
        """
        Classifies the user's message to determine if it's about a complaint,
        complaint status, notification preference, or regular conversation.
        """
        classification_prompt = f"""
        Classify the following message into one of these intents:
        1. "complaint" - If the message is a complaint that needs to be logged. Make sure to analyse properly before you conclude something is a complaint or not.
        e.g, a user might say "they think they have a complaint"... In such cases, encourage them to share details. Do not classify non-complaint as complaint.
        
        2. "get_complaint_status" - If the user wants to know what the status of an existing complaint is.
        3. "change_notification_preference" - If the user wants to update their notification preferences.
        4. "regular_convo" - If the message is part of a normal conversation that doesn't relate to complaints
        or the user says they think they have a complaint or something of such nature.

        Message:
        "{input_string}"
        
        Respond with ONLY one of the following:
        - complaint
        - get_complaint_status
        - change_notification_preference
        - regular_convo
        """
        response = self.llm.invoke(classification_prompt).content.strip().lower()
        return response


    def extract_complaint_details(self, input_string: str):
        """
        Extracts complaint details such as complaint text, topics, and status.
        """
        extraction_prompt = f"""
        Extract the following complaint details from the message:
        - Date: Current date
        - Complaint Text: Detailed description of the issue
        - Complaint Topic 1: Primary category of complaint
        - Complaint Topic 2: Secondary category (if applicable)
        - Receive Update: "yes"
        - Status: "pending"

        Respond in strict JSON format:
        {{
             "date": "YYYY-MM-DD",
             "complaint_text": "...",
             "complaint_topic_1": "...",
             "complaint_topic_2": "...",
             "receive_update": "yes",
             "status": "pending"
        }}
         

        Message to extract: "{input_string}"
        """
        complaint_json = self.llm.invoke(extraction_prompt).content
        complaint_data = json.loads(complaint_json)
        return complaint_data


    def lodge_complaint_to_db(self, complaint_data):
        """
        Logs the complaint to the database and returns the complaint ID.
        """
        complaint_id = lodge_complaint(json.dumps(complaint_data))
        return complaint_id
    

    def get_complaint_status(self, complaint_id: str):
        """
        Retrieves the status of a complaint based on the complaint ID.
        """
        return db_get_complaint_status(complaint_id)


    def update_notification_status(self, complaint_id: str, new_status: str, users_first_name):
        """
        Updates the notification preference for a given complaint.
        """
        new_stat, topic = change_notification_preference(complaint_id, new_status)

        if new_stat == "no":
            message = f"Alright {users_first_name}, you will no longer receive updates on your report about {topic}"
            
        elif new_stat == "yes":
            message = f"Sure thing {users_first_name}, you will now be receiving updates on your report about {topic}"

        return message


    def handle_message(self, input_string: str, context_and_meta: str, users_first_name):
        """
        Main handler that processes the user's message based on the classified intent.
        """
        intent = self.classify_intent(input_string)
        
        if intent == "complaint":
            # Extract complaint details
            complaint_data = self.extract_complaint_details(input_string)
            complaint_id = self.lodge_complaint_to_db(complaint_data)
            
            response = (
                "Sorry about the inconvenience, your complaint has been logged  \n\nComplaint ID \\(Click to copy\\):"
                f"  **\n\n`{complaint_id}`**"
        )
            
        elif intent == "get_complaint_status":
            complaint_id = self.extract_complaint_id(input_string)
            status = self.get_complaint_status(complaint_id)
            response = f"Your complaint status is: {status}"

        elif intent == "change_notification_preference":
            complaint_id, new_status = self.extract_id_and_new_status(input_string)
            response = self.update_notification_status(complaint_id, new_status, users_first_name)

        else:
            response = self.generate_general_response(input_string, context_and_meta)
        return response


    def extract_id_and_new_status(self, input_string: str):
        """
        Extracts complaint ID and new status (yes/no) for updating preferences.
        """
        extraction_prompt = f"""
        Check and extract:
            - "complaint_id": "<complaint_id>"
            - "new_status": "<new_status>"  # Only if updating notification preferences. This should be yes/no

        Return only the extracted details in JSON format:
        Message to extract from: "{input_string}"
        """
        extraction_response = self.llm.invoke(extraction_prompt).content
        extracted_data = json.loads(extraction_response)
        return extracted_data.get("complaint_id"), extracted_data.get("new_status")


    def extract_complaint_id(self, input_string: str):
        """
        Extracts the complaint ID from the user's input string.
        """

        extraction_prompt = f"""
        Extract the Complaint ID from the following message:
        "{input_string}"

        Respond only with the complaint ID.
        """
        return self.llm.invoke(extraction_prompt).content.strip()


    def generate_general_response(self, input_string: str, context_and_meta:str):
        """
        Generates a general response for messages that don't relate to a complaint.
        """
        response_prompt = f"""
        Provide a helpful, conversational response to:
        "{input_string}"

        The following is some meta-data about the user and context:
        "{context_and_meta}"

        Keep responses short and always in first-person place without mentioning the metadata.
        You can refer to the user using their name or date where necessary but never repeat verpose metadata or context that isnt necessary
        One more thing, you need to project company image so never engage in any slander that may come as a reslt of users input.
        """
        return self.llm.invoke(response_prompt).content