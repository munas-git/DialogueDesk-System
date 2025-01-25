# langchain & NLP related
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# others
import io
from config import *
from MongoDBOps import *
from typing import BinaryIO


# silencing warnings
import warnings
warnings.filterwarnings('ignore')

whisper_client = OpenAI(api_key=OPEN_AI_KEY)


def audio_to_transcript(audio_file: BinaryIO) -> str:
    def split_audio(file: BinaryIO, chunk_size: int = 25 * 1024 * 1024) -> list:
        """
        Splits a file-like object into chunks of the specified size (in bytes).
        """
        file.seek(0)  # Ensure we start reading from the beginning
        chunks = []
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            chunk_io = io.BytesIO(chunk)
            chunk_io.name = audio_file.name  # Retain original file name
            chunks.append(chunk_io)
        file.seek(0)  # Reset the pointer after splitting
        return chunks

    # Check the file size
    audio_file.seek(0, 2)  # Move to the end of the file
    file_size = audio_file.tell()
    audio_file.seek(0)  # Reset pointer to the start

    if file_size > 25 * 1024 * 1024:  # File exceeds 25 MB
        chunks = split_audio(audio_file)
        transcripts = []
        for idx, chunk in enumerate(chunks):
            print(f"Processing chunk {idx + 1} of {len(chunks)}...")
            transcription = whisper_client.audio.transcriptions.create(
                model="whisper-1", 
                file=chunk
            )
            transcripts.append(transcription.text)
        return " ".join(transcripts)
    else:  # File is within size limit
        transcription = whisper_client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        return transcription.text
    

def generate_transcript_insights(transcript: str) -> dict:
    response_schemas = [
        ResponseSchema(name = "Summary", description = "A well-written string summary from the meetings transcript."),
        ResponseSchema(name = "key_points_discussed", description = "A python list [...] of key points discussed in the transcript."),
        ResponseSchema(name = "action_items", description = "A python list [...] of actionable items from the transcript."),
    ]

    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    system_message = SystemMessagePromptTemplate.from_template(
        "You are an assistant skilled at summarizing and extracting insights from meetings data for high-level organizations, meaning TOP QUALITY OUTPUT ONLY. ake sure to be exhaustive about the key points and action points as well."
    )

    template = """
    Analyze the following transcript and extract insights. Format the insights as JSON:
    Transcript: {input_transcript}

    {format_instructions}
    """
    
    human_message = HumanMessagePromptTemplate.from_template(template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    llm = ChatOpenAI(model = "gpt-3.5-turbo", temperature = 0, max_tokens = 1000, openai_api_key = OPEN_AI_KEY)
    chain = chat_prompt | llm
    
    response = chain.invoke({
        "input_transcript": transcript,
        "format_instructions": output_parser.get_format_instructions()
    })
    
    insights = output_parser.parse(response.content)
    
    return insights


class Agent():
    def __init__(self):
        self.tools = [
            Tool(
                name="meetings_metadata_by_date",
                func=meetings_metadata_by_date,
                description=(
                    "MongoDB function to retrieve meetings day metadata"
                    "Use this tool whenever you need to find out the number of meetings held on a particular day "
                    "(no_of_meetings) or the meeting ids (meeting_ids) of meetings held on a particular day. "
                    "Input should simply be a date in year-month-day format e.g 2025-01-22. "
                    "The function should be used to answer questions such as how many meetings were held on the second "
                    "day of january in 2023... That date would translate to: 2023-01-02 and you would call the function "
                    "as follows: meetings_metadata_by_date(date); Then you can answer the question based on the output. Remember to pass the date as a string."
                    "Another likely usecase of this function could be used to retrieve meeting IDs from the database "
                    "and pose follow up questions for a user. If a user asks about a specific date's meeting, first "
                    "check the meeting IDs using meetings_metadata_by_date('DATE')['meeting_ids']. If multiple meetings "
                    "exist, ask for clarification, what particular meeting. If only one exists, use search_by_date_and_id. If none exist, "
                    "inform the user no recordings are available."
                )
            ),
            Tool(
                name="search_by_date_and_id",
                func=search_by_date_and_id,
                description=(
                    "MongoDB function to retrieve meetings day complete data such as transcript and more"
                    "Use this tool whenever you need to retrieve information and answer questions from details within "
                    "transcript, summary, key points or action items from information of a specific date and meeting id. "
                    "The function input is passed as a tuple like so for the first meeting on January 2nd of 2023:"
                    "(date, meeting_id)"
                    "An example meeting id is 'Meeting - 18:15'. The output will include transcript, ai_summary, key_points, and action_items fields."
                    "The output of this function is a dictinary with the following keys"
                    "'transcript' which is a string transcript" 
                    "'ai_summary' which is a string summary generated by ai"
                    "key_points which is a list containing key points discussed in the meeting"
                    "action_items which is a list containing action points from the meeting."
                    "You can then work with that information to asnwer the question as necessary"
                    "If no info is returned from this tool or empty topics, just state that that information is not available"
                )
            ),
            Tool(
                name="get_todays_date",
                func=get_todays_date,
                description=(
                    "This tool simply retrieves the current date and returns it in this format: YYYY-MM-DD. "
                    "Use this whenever you need to answer questions relative to the current day, such as: "
                    "'Was there any meeting today?', 'What was discussed in today's meeting?', etc."
                )
            )
        ]
        
        template = f"""
        You are an advanced assistant specializing in meeting and complaints data analysis. Your primary objective is to help workers efficiently retrieve and analyze meeting information with precision and context awareness.

        Context Constraints:
        - Strictly focus on meeting and complaints-related insights
        - If a query deviates from business operations, politely redirect the conversation
        - When users ask follow-up questions, refer to previous context to provide comprehensive answers

        Specific Context Handling Instructions (VERY VERY IMPORTANT):
        - If a user references a previous query or seeks clarification, use the conversation context above to provide precise, relevant information
        - Look for patterns, dependencies, and continuity in the conversation
        - Be prepared to reference specific details from earlier messages

        Context Guidelines:
        1. Always carefully review the provided conversation context before responding.
        2. Use the context to:
        - Understand the conversation's progression
        - Provide more accurate and relevant responses
        - Maintain continuity in the conversation
        - Reference previous interactions when appropriate

        Response Protocol:
        - For non-meeting or non-complaints related questions: 
        'My sole purpose is to assist you with meetings or complaints insights. I cannot help with that at the moment.'
        - Maintain a professional, concise, and helpful tone
        - Engage in minimal friendly greetings
        - Prioritize information retrieval and analysis
        """
        
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            max_tokens=800,
            timeout=None,
            max_retries=2,
            api_key=OPEN_AI_KEY,
        )
        
        
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent="zero-shot-react-description",
            verbose=True,
            handle_parsing_errors=True,
            agent_kwargs={
                "system_message": template
            }
        )

    def answer(self, query):
        try:
            response = self.agent.invoke({"input": query})
            return response["output"] if isinstance(response, dict) else response
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            return "Oh ohh... Something seems to be wrong with my head, kindly ask admin to check up on me 🤧😷"
    

def analyse_affected_users():
    """Function checks all active complaints and messages users who's topics were brought up during just uploaded meeting."""
    pass