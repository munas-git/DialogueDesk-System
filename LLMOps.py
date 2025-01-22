# langchain & NLP related
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# others
import io
from config import *

whisper_client = OpenAI(api_key=OPEN_AI_KEY)


def audio_to_transcript(audio_file) -> str:
    
    audio_bytes = audio_file.read()
    audio_io = io.BytesIO(audio_bytes)
    audio_io.name = audio_file.name

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
        "You are an assistant skilled at summarizing and extracting insights from meetings data for high-level organizations, meaning TOP QUALITY OUTPUT ONLY."
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