import streamlit as st

# Data manipulation
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

# Data visualisations
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Others
import datetime

# LLM/Agent related
from LLMOps import audio_to_transcript, generate_transcript_insights


# page settings
st.set_page_config(
    page_title="BUSA Connect Dashboard",
    page_icon=":bar_chart:",
    layout="wide"
)

# dataframes...
complaints_data = pd.read_csv("dataset/student-complaints.csv")

# Display mode color light/dark... might move to session state later
bg_color = "white"
n_grams = (2,3) # for word cloud

# Initialise session states
if "meeting_insight_date" not in st.session_state: # Viewing insight for meating
    st.session_state.meeting_insight_date = datetime.date.today()

if "meeting_date" not in st.session_state: # Uploading meeting for today or past date
    st.session_state.meeting_date = datetime.date.today()

# Initialising session state for chat
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Sidebar for filters
st.sidebar.header("Meetings Filter")
meeting_insight_date = st.sidebar.date_input(
    "Select Meeting Date:",
    value=datetime.date.today(),
    min_value=datetime.date(2006, 1, 1),
    max_value=datetime.date.today(),
    key="meeting_date_insight"
)
# Updating date in session state
st.session_state.meeting_insight_date = meeting_insight_date
st.sidebar.divider()

st.sidebar.header("Meeting Recording Upload")
# Select the date for the meeting upload
meeting_date = st.sidebar.date_input(
    "Select Recording Date:",
    value=datetime.date.today(),
    min_value=datetime.date(2006, 1, 1),
    max_value=datetime.date.today(),
    key="meeting_date_upload" 
)

# File uploader widget
uploaded_file = st.sidebar.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "flac", "webm"])
sidebar_status = st.sidebar.empty()

import time
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

                # Clear status messages and returning info (temp till fix)
                sidebar_status.empty()
                st.sidebar.success("Processing complete!")
                st.write(insights)
else:
    st.sidebar.info("No file uploaded yet")
st.sidebar.divider()


# Sidebar for chat
with st.sidebar:
    st.title("🤖 AI Senator")

    # Chat container
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
        answer = "Implement soon..."
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        messages.chat_message("assistant").write(answer)


# KPIs
no_of_complaints = len(complaints_data["complaint_id"])

st.title("📊 Complaints Insight Dashboard")
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
    display_df = pd.DataFrame(complaints_filtered_df.head(5)["complaint_text"].tolist(), columns=["Complaints"])
    st.dataframe(display_df)

st.divider()
st.markdown("<h2 style='text-align: center;'>Meeting Insights Section</h2>", unsafe_allow_html=True)