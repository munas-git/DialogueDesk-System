# lang graph specific
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from typing import TypedDict, List, Annotated

# others
import json
import operator
from config import OPEN_AI_KEY
from ComplaintsMongoDBOps import *
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    max_tokens=800,
    api_key=OPEN_AI_KEY
)


class AgentState(TypedDict):
    messages: Annotated[List[dict], operator.add]
    complaint_data: dict
    is_complaint: bool

class DialogueDeskAgent:
    def __init__(self):
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            max_tokens=800,
            api_key=OPEN_AI_KEY
        )

        # building workflow graph
        self.workflow = StateGraph(AgentState)

        # nodes here
        self.workflow.add_node("determine_intent", self.determine_intent)
        self.workflow.add_node("extract_complaint_details", self.extract_complaint_details)
        self.workflow.add_node("lodge_complaint", self.lodge_complaint_to_db)
        self.workflow.add_node("general_response", self.general_response)

        # conditional routing
        def route(state: AgentState):
            return "extract_complaint_details" if state.get("is_complaint", False) else "general_response"

        # edges
        self.workflow.add_conditional_edges("determine_intent", route)
        self.workflow.add_edge("extract_complaint_details", "lodge_complaint")
        self.workflow.add_edge("lodge_complaint", END)
        self.workflow.add_edge("general_response", END)

        # entry point & graph compilation.
        self.workflow.set_entry_point("determine_intent")
        self.app = self.workflow.compile()


    def determine_intent(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]["content"]
        
        classification_prompt = f"""
        Classify if the following message is a complaint that needs to be logged:
        "{last_message}"
        
        Respond with ONLY 'YES' or 'NO':
        """
        
        response = self.llm.invoke(classification_prompt).content.strip().upper()
        
        return {
            'is_complaint': response == 'YES',
            'complaint_data': {} if response != 'YES' else None
        }

    def extract_complaint_details(self, state: AgentState):
        last_message = state['messages'][-1]['content']
        
        complaint_extraction_prompt = f"""
        Extract the following complaint details from the message:
        - Date: Current date
        - Complaint Text: Detailed description of the issue
        - Complaint Topic 1: Primary category of complaint
        - Complaint Topic 2: Secondary category (if applicable)
        
        Respond in strict JSON format:
        {{
            "date": "YYYY-MM-DD",
            "complaint_text": "...",
            "complaint_topic_1": "...",
            "complaint_topic_2": "...",
            "receive_update": "yes",
            "status": "pending"
        }}
        
        Message to extract: "{last_message}"
        """
        
        complaint_json = self.llm.invoke(complaint_extraction_prompt).content
        complaint_data = json.loads(complaint_json)
        
        return {'complaint_data': complaint_data}

    def lodge_complaint_to_db(self, state: AgentState):
        complaint_data = state['complaint_data']
        complaint_id = lodge_complaint(json.dumps(complaint_data))
        
        return {
            'messages': [
                AIMessage(content=f"Your complaint has been logged. Complaint ID: <code>{complaint_id}</code>")
            ]
        }

    def general_response(self, state: AgentState):
        last_message = state['messages'][-1]['content']
        
        response_prompt = f"""
        Provide a helpful, conversational response to:
        "{last_message}"
        
        If the query seems related to a complaint or report, guide the user on how to proceed.
        """
        
        response = self.llm.invoke(response_prompt).content
        
        return {
            'messages': [AIMessage(content=response)]
        }

    async def answer(self, query):
        inputs = {
            'messages': [{'content': query}]
        }
        
        response = await self.app.ainvoke(inputs)
        return response['messages'][-1].content