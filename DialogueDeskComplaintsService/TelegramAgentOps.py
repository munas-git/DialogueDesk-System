# Langchain related
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool

# others
import asyncio
from config import OPEN_AI_KEY
from ComplaintsMongoDBOps import *


class AsyncAgent:
    def __init__(self):
        self.tools = [
            Tool(
                name="lodge_complaint",
                func=self._sync_wrapper(lodge_complaint),
                description="""
                    Purpose:
                        This tool allows the chatbot to accept and upload a user's complaint to a NoSQL database.
                        The complaint is submitted as a JSON object, which contains relevant details such as;
                        the complaint text, related topics, whether the user wants updates, and the current status of the complaint.

                    Input json input expected are as follows:
                    complaint_text (User's complaint or issue description)
                    complaint_topics (a list containing two topics that describe the complaint),
                    receive_update (yes or no),
                    status: (resolved or (pending)

                    receive update should be yes by default and status should be pending by default.

                    Remember to tell the user their complaint id which is returned after succesful call of this function. 
                """
            ),
            # Tool(
            #     name="MongoDB function to retrieve meetings day complete data such as transcript and more",
            #     func=self._sync_wrapper(self.async_get_meetings_data),  # Replace with your async function
            #     description="Retrieve full meeting data including transcripts from MongoDB."
            # )
        ]

        # Define a system message template (replace with your actual template)
        self.system_message = """
        You are an AI Assistant chatbot designed to interact with users and assist them effectively.

        Your name is DialogueDeskBot
        Your Bio: The peoples' voices, amplified. I ensure your concerns reach the right audience, & keep you posted too.

        Your purpose is to help individuals with the following tasks:
        **Commands**
        /start - Start the bot and introduce yourself.
        /help - Provide guidance on how to use the bot.
        /make_report - Submit a complaint or report an issue (e.g. technical, service-related).
        /report_update - Check the status of an existing report (use an ID if multiple complaints exist).
        /cancel_notifications - Stop receiving notifications about the progress of one or all complaints.
        /receive_notifications - Resume notifications about one or all complaints.

        **How You Work**
        - If a user describes a problem or complaint, acknowledge it politely, log the issue, and let them know they will be updated.
        - If a user asks for a report update, retrieve the status and provide a concise update.
        - If a user wants to manage notifications, handle their request to either stop or resume notifications.
        - If the user is unsure, respond with helpful information and suggest the available commands.
        - Always respond with empathy and precision, ensuring the user feels heard and supported.
        
        **Tone**
        - Empathetic: Acknowledge the user's concerns and show understanding.
        - Proactive: Anticipate what the user might need and offer helpful suggestions.
        - Informative: Keep responses concise while providing all necessary details.
        """

        # Initialize the LLM with asynchronous support
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            max_tokens=800,
            timeout=None,
            max_retries=2,
            api_key=OPEN_AI_KEY
        )

        # Initialize the agent
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent="zero-shot-react-description",
            verbose=True,
            handle_parsing_errors=True,
            agent_kwargs={
                "system_message": self.system_message
            }
        )

    # Async method to handle a query
    async def answer(self, query):
        try:
            # Use the asynchronous method to invoke the agent
            response = await self.agent.ainvoke({"input": query})
            return response
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            return "Oh ohh... I can't respond right now. Please try again later 🤧😷"

    
    def _sync_wrapper(self, async_func):
        """Wraps an async function to make it compatible with sync calls."""
        def sync_func(*args, **kwargs):
            return asyncio.run(async_func(*args, **kwargs))
        return sync_func
