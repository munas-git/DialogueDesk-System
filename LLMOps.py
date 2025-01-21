# langchain & NLP related
from openai import OpenAI

# others
import io
from config import *

client = OpenAI(api_key=OPEN_AI_KEY)

def audio_to_transcript(audio_file) -> str:
    
    audio_bytes = audio_file.read()
    audio_io = io.BytesIO(audio_bytes)
    audio_io.name = audio_file.name

    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file
    )
    return transcription.text


def generate_transcript_insights(transcript: str) -> str:
    prompt = f"""
    Analyze the following transcript and extract insights. Format the insights as JSON:
    Transcript: {transcript}

    JSON Output:
    {{
        "Summary": ["..."],
        "key_points_discussed": ["..."],
        "action_items": ["..."]
    }}
    """

    # OpenAI API call
    response = client.chat.completions(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are an assistant skilled at summarizing and extracting insights from text transcripts for high level organisations meaning TOP QUALITY OUTPUT ONLY"},
                  {"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7,
    )

    return response['choices'][0]['message']['content']