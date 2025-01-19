import streamlit as st

# Data manipulation
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

# Data visualisations
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt


# page settings
st.set_page_config(
    page_title="BUSA Connect Dashboard",
    page_icon=":bar_chart:",
    layout="wide"
)

# dataframes...
complaints_data = pd.read_csv("student-complaints.csv")
event_data = pd.read_csv("events.csv")
events_feedback = pd.read_csv("event-feedback.csv")

# Display mode color light/dark... might move to session state later
bg_color = "white"

# Initialise session state for filters
if "filters" not in st.session_state:
    st.session_state.filters = {
        "event_name": event_data["event_name"].unique().tolist(),
    }

# Initialising session state for chat
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Sidebar for filters
st.sidebar.header("Select Filters Here")
event_name = st.sidebar.selectbox(
    "Event name",
    options=event_data["event_name"],
    on_change=lambda: st.session_state.filters.update({"event_name": event_name})
)
event_id = event_data["event_id"][event_data["event_name"] == event_name].iloc[0]

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


# df filter on events_feedback data affected by event name
feedback_df_by_event = events_feedback.query(
    "event_id == @event_id "
)

# KPIs
no_of_complaints = len(complaints_data["complaint_id"])
no_of_events = len(events_feedback["event_id"].unique())

st.title("📊 Complaints & Events Insight Dashboard")
st.markdown("##")


# Display KPIs
first_col, second_col = st.columns(2)
# first_col, second_col, third_col, forth_col = st.columns(4)

with first_col:
    st.subheader(f"No. of Complaints: {no_of_complaints:,}")
with second_col:
    st.subheader(f"No. of Events: {no_of_events:,}")


# Graphs building #
# 1. Line graph of number of complaints per day
complaints_per_day = complaints_data.groupby("date").size().reset_index(name="num_complaints")

# Create the interactive line graph with Plotly Express
complaints_per_day_fig = px.line(
    complaints_per_day,
    x='date',
    y='num_complaints',
    labels={'date': 'Date', 'num_complaints': 'Number of Complaints'},
    markers=True,
)

complaints_per_day_fig.update_layout(
    title=dict(
        text="Number of Complaints Per Day",
        x=0.5, # Centering
        font=dict(size=15)
    ),
    width=400,
    height=300,
    margin=dict(t=27, b=0, l=0, r=0),
    showlegend=False,
    xaxis_showgrid=False,
    yaxis_showgrid=False,
    plot_bgcolor=bg_color,
    paper_bgcolor=bg_color
)


# 2. Wordcloud showing most common non-stopword bi and tri-grams.
vectorizer = CountVectorizer(ngram_range=(2, 3), stop_words="english")
X = vectorizer.fit_transform(complaints_data["complaint_text"])
ngrams = vectorizer.get_feature_names_out()

# Generate n-gram frequencies
ngram_frequencies = dict(zip(ngrams, X.toarray().sum(axis=0)))

# Generate the word cloud
wordcloud = WordCloud(width=400, height=300, background_color=bg_color).generate_from_frequencies(ngram_frequencies)

complaints_ngrams_fig, ax = plt.subplots(figsize=(10, 5))
ax.imshow(wordcloud, interpolation="bilinear")
ax.axis("off")


# Display Visuals
second_first_col, second_second_col = st.columns(2)

with second_first_col:
    st.plotly_chart(complaints_per_day_fig)
    st.markdown("#### Word Cloud of N-Grams")
    st.pyplot(complaints_ngrams_fig)
# with second_first_col: