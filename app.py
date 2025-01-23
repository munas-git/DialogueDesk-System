# cool name idea: DialogueDesk

import streamlit as st

# Data manipulation
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

# Data visualisations
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Others
import re
import time
import json
import datetime

# LLM/Agent related
from LLMOps import audio_to_transcript, generate_transcript_insights, Agent

# db related
from MongoDBOps import *


# page settings
st.set_page_config(
    page_title="DialogueDesk Dashboard",
    page_icon=":bar_chart:",
    layout="wide"
)

# dataframe and AI Agent
complaints_data = pd.read_csv("dataset/student-complaints.csv")

# Display mode color light/dark... might move to session state later
bg_color = "white"
n_grams = (2,3) # for word cloud

# ===================================================================================================
# Initialise session states
if "meeting_insight_date" not in st.session_state: # Viewing insight for meating
    st.session_state.meeting_insight_date = datetime.date.today()

if "meeting_date" not in st.session_state: # For uploading meeting for today or past date
    st.session_state.meeting_date = datetime.date.today()

if "meeting_time" not in st.session_state: # For uploading meeting for today or past date
    st.session_state.meeting_time = datetime.date.today()

# Initialising session state for chat
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "selected_meeting_id" not in st.session_state: # for retrieving meeting insights
    st.session_state.selected_meeting_id = None

if "meeting_insights" not in st.session_state:
    st.session_state.meeting_insights = None
# ===================================================================================================


st.sidebar.header("Upload Meeting Recording.")
# Select the date for the meeting upload
meeting_date = st.sidebar.date_input(
    "Select Meeting Date:",
    value=datetime.date.today(),
    min_value=datetime.date(2006, 1, 1),
    max_value=datetime.date.today(),
    key="meeting_date_upload" 
)
meeting_time = st.sidebar.time_input(
        "Select Meeting Time:", 
        value=datetime.time(12, 0)  # Default afternoon
    )

meeting_date = meeting_date.strftime('%Y-%m-%d')
meeting_time = meeting_time.strftime('%H:%M')


# File uploader widget
uploaded_file = st.sidebar.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "flac", "webm"])
sidebar_status = st.sidebar.empty()


# Only show submit button if a file is uploaded
if uploaded_file is not None:
    # Add submit button to sidebar
    if st.sidebar.button("Process Audio File"):
        # Show loading status in sidebar
        with st.sidebar:
            with st.spinner("Processing your audio file..."):
                sidebar_status.text("Step 1: Extracting Transcript...")
                transcript = audio_to_transcript(uploaded_file)
                
                sidebar_status.text("Step 2: Generating Insights...")
                insights = generate_transcript_insights(transcript)                
                
                sidebar_status.text("Step 3: Uploading Insights to DB...")
                time.sleep(1)

                # Clear status messages and returning info
                sidebar_status.empty()
                st.sidebar.success("Process Completed!")
                

                meeting_data = {
                    "Date": meeting_date,
                    "meeting_id": f"Meeting - {meeting_time}", 
                    "transcript": transcript, 
                    "ai_summary": insights.get("Summary", "No summary available"),
                    "key_points" : insights.get("key_points_discussed", []),
                    "action_items" : insights.get("action_items", []) 
                }

                # Uploading the data --- If data says uploaded but doesnt reflect on db, check and move this aspect above process completed.
                upload_data(meeting_data)

else:
    st.sidebar.info("No file uploaded yet")
st.sidebar.divider()


# Extracting past 10 messages then re-ordering so that last entered (most recent) can be first for context.
context = st.session_state.chat_messages[-10:][::-1]
formatted_context = "\n".join(f"{message['role']}: {message['content']}" for message in context)
agent = Agent()

# Sidebar for chat
with st.sidebar:
    st.title("🤖 AI Representative")

    # Chat input
    messages = st.container(height=300)
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            messages.chat_message("user").write(msg["content"])
        elif msg["role"] == "assistant":
            messages.chat_message("assistant").write(msg["content"])

    # Chat input
    if new_prompt := st.chat_input("How can I assist?"):
        
        # state magangment...
        st.session_state.chat_messages.append({"role": "user", "content": new_prompt})
 
        # display output instantly for chat history
        messages.chat_message("user").write(new_prompt)

        # generate RAG AI response & add to sesion state as well
        # answer = agent.answer(f"This is the conversation history, make sure to ansert conversation history related questions with this\n{formatted_context}\n\n This is the new prompt now: {new_prompt}")
        conversation_history = (
            "This is the conversation history, make sure to answer conversation "
            "history-related questions such as what was my last question, follow up questions and anything that depends on the last conersation with this\n"
            f"{formatted_context}\n\n"
        )

        new_prompt_instruction = f"This is the new prompt for you to answer now: {new_prompt}"

        # Combine the history and new prompt
        answer = agent.answer(f"{conversation_history}{new_prompt_instruction}")
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        messages.chat_message("assistant").write(answer)
        

# KPIs
no_of_complaints = len(complaints_data["complaint_id"])

st.title("🗣 DialogueDesk Dashboard.")
st.markdown("##")


# Display KPIs
first_col, second_col = st.columns(2)

with first_col:
    st.subheader(f"No. of Complaints: {no_of_complaints:,}")

st.divider()

# Graphs building
# Line graph of number of complaints per day
complaints_per_day = complaints_data.groupby("date").size().reset_index(name="num_complaints")
complaints_per_day_fig = px.line(
    complaints_per_day,
    x='date',
    y='num_complaints',
    labels={'date': 'Date', 'num_complaints': 'Number of Complaints'},
    markers=True,
)

complaints_per_day_fig.update_layout(
    title=dict(
        text="Complaints Per Day",
        x=0.4, # Centering
        font=dict(size=15)
    ),
    width=600,
    height=300,
    margin=dict(t=27, b=0, l=0, r=0),
    showlegend=False,
    xaxis_showgrid=False,
    yaxis_showgrid=False,
    plot_bgcolor=bg_color,
    paper_bgcolor=bg_color
)


# Wordcloud showing most common complaints non-stopword bi and tri-grams.
complaints_vectorizer = CountVectorizer(ngram_range=n_grams, stop_words="english")
X_complaints = complaints_vectorizer.fit_transform(complaints_data["complaint_text"])
complaints_ngrams = complaints_vectorizer.get_feature_names_out()

# Generate n-gram frequencies
complaints_ngram_frequencies = dict(zip(complaints_ngrams, X_complaints.toarray().sum(axis=0)))

# Generate the word cloud
complaints_wordcloud = WordCloud(width=600, height=470, background_color=bg_color).generate_from_frequencies(complaints_ngram_frequencies)

complaints_ngrams_fig, ax = plt.subplots(figsize=(10, 5))
ax.imshow(complaints_wordcloud, interpolation="bilinear")
ax.set_title("Magnitude of Complaints", fontsize=15)
ax.axis("off")


# Display Visuals:
second_first_col, second_second_col, second_third_col = st.columns(3)
with second_first_col:
    st.plotly_chart(complaints_per_day_fig)
with second_second_col:
    st.pyplot(complaints_ngrams_fig)
with second_third_col:
    # searchable dataframe for event reviews
    complaints_search_term = st.text_input("Search complaints:", "").split(" ")

    # Filter DataFrame based on search term
    if complaints_search_term:
        complaints_filtered_df = complaints_data[complaints_data["complaint_text"].apply(lambda x: all(term.lower() in str(x).lower() for term in complaints_search_term))]
    else:
        complaints_filtered_df = complaints_data

    # Display the filtered DataFrame
    display_df = pd.DataFrame(complaints_filtered_df["complaint_text"].tolist(), columns=["Complaints"])
    st.dataframe(display_df,  use_container_width = True, height = 230)
st.divider()


# Meeting insights section #
st.markdown("<h2 style='text-align: center;'>Meeting Insights Section</h2>", unsafe_allow_html=True)
date_filter_col, meeting_id_filter, _, _, _, _, = st.columns(6) # temporaty hack to make the date selection column look smaller.

with date_filter_col:
    # Date input
    meeting_insight_date = st.date_input(
        "Select Meeting Date:",
        value=datetime.date.today(),
        min_value=datetime.date(2006, 1, 1),
        max_value=datetime.date.today(),
        key="meeting_date_insight"
    )
    meeting_insight_date = meeting_insight_date.strftime('%Y-%m-%d')


# Check if the selected date has more than one meeting recorded for the day... select meeting id pops up beside the date selection.
days_meetings_meta = meetings_metadata_by_date(meeting_insight_date)
no_of_meetings, meeting_ids = days_meetings_meta["no_of_meetings"], days_meetings_meta["meeting_ids"]

if no_of_meetings > 1:
    with meeting_id_filter:
        selected_meeting_id = st.selectbox("Select Meeting ID:", meeting_ids)
else:
    selected_meeting_id = "Meeting 1" ####################


# Check if there is need to fetch new data [state change or meeting_date (upload date) = meeting_insight_date (selected date for insight)]
if (
    meeting_insight_date != st.session_state.meeting_insight_date
    or selected_meeting_id != st.session_state.selected_meeting_id
    or (meeting_date == meeting_insight_date and st.session_state.get("transcript") == "None available at the moment") # meaning that the just uploaded data hasnt been retrieved
):
    # Update session state with new parameters
    st.session_state.meeting_insight_date = meeting_insight_date
    st.session_state.selected_meeting_id = selected_meeting_id

    # Retrieve and store data in session state
    st.session_state.meeting_insights = search_by_date_and_id(
        f"{meeting_insight_date}, {selected_meeting_id}"
    )

meeting_insights = st.session_state.meeting_insights
mode = st.radio("Choose mode", ("Transcript", "Summary"))

if meeting_insights:
    meeting_key_points = meeting_insights["key_points"]
    meeting_action_items = meeting_insights["action_items"]
    meeting_transcript = meeting_insights["transcript"]
    meeting_ai_summary = meeting_insights["ai_summary"]
    text_content = meeting_transcript if mode == "Transcript" else meeting_ai_summary
else:
    meeting_key_points = []
    meeting_action_items = []
    meeting_transcript = "No meeting insights available. Please check the date and ID."
    meeting_ai_summary = "No meeting insights available. Please check the date and ID."
    text_content = meeting_transcript if mode == "Transcript" else meeting_ai_summary


st.markdown("""
<style>
    .fixed-text-box {
        border: 1px solid #ccc;
        padding: 10px;
        border-radius: 5px;
        background-color: white;
        height: 200px;
        overflow-y: auto;
        color: #31333F;
        font-size: 1rem;
        line-height: 1.5;
        font-family: "Source Sans Pro", sans-serif;
    }
    .highlight {
        background-color: #ffeb3b;
        padding: 0.1em 0;
    }
    .search-stats {
        font-size: 0.9rem;
        color: #666;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

def highlight_text(text, search_term):
    """
    Highlight search term in text while preserving newlines.
    Returns tuple of (highlighted_text, match_count).
    """
    if not search_term:
        return text, 0
    
    try:
        # Escape special characters in search term
        search_term = re.escape(search_term)
        
        # Split text into lines to preserve newlines
        lines = text.split('\n')
        highlighted_lines = []
        match_count = 0
        
        for line in lines:
            # Count matches in this line
            matches = len(re.findall(search_term, line, re.IGNORECASE))
            match_count += matches
            
            # Replace matches with highlighted version
            if matches > 0:
                pattern = f'({search_term})'
                repl = r'<span class="highlight">\1</span>'
                line = re.sub(pattern, repl, line, flags=re.IGNORECASE)
            
            highlighted_lines.append(line)
        
        return '\n'.join(highlighted_lines), match_count
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return text, 0


# Create a container for the search interface
search_container = st.container()
with search_container:
    # Create a search input field
    search_term = st.text_input(f"Search in {mode}:", "")

    try:
        # Highlight matches and count them
        highlighted_text, match_count = highlight_text(text_content, search_term.strip())
        
        # Display search stats if there's a search term
        if search_term:
            st.markdown(f'<div class="search-stats">Found {match_count} matches</div>', 
                       unsafe_allow_html=True)
        
        # Display the text with highlights
        st.markdown(f"### Meeting {mode}.")
        st.markdown(f'<div class="fixed-text-box">{highlighted_text}</div>', 
                   unsafe_allow_html=True)
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    

# Creating df containing Key Points and Action Items
key_points_df = pd.DataFrame(meeting_key_points, columns=["Key Points"])
action_points_df = pd.DataFrame(meeting_action_items, columns=["Action Points"])

# Meeting key info section
st.markdown(f"#### Take Aways...")
third_first_col, third_second_col = st.columns(2)

with third_first_col:
    st.dataframe(key_points_df, use_container_width = True, height = 200)
with third_second_col:
    st.dataframe(action_points_df, use_container_width = True, height = 200)