# langchain & NLP related
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# others
import io
from config import *
from typing import BinaryIO

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

