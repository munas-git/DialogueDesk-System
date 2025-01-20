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
n_grams = (2,3) # for word cloud

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

with first_col:
    st.subheader(f"No. of Complaints: {no_of_complaints:,}")
with second_col:
    st.subheader(f"No. of Events: {no_of_events:,}")

st.markdown("---")

# Graphs building
# Line graph of number of complaints per day
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
ax.axis("off")


# Pie chart of positive Vs negative reviews
sentiment_count = feedback_df_by_event["sentiment"].value_counts().reset_index(name='count')
sentiment_count.columns = ["sentiment", "count"]

# Create the pie chart with Plotly Express
sentiment_pie_chart = px.pie(
    sentiment_count, 
    names="sentiment", 
    values="count", 
    color="sentiment",
    color_discrete_map={"positive": "green", "negative": "red"}
)
sentiment_pie_chart.update_layout(
    title=dict(
        text="Positive vs Negative Complaints",
        x=0.3, # Centering
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


# Wordcloud showing most common events feedback non-stopword bi and tri-grams
events_vectorizer = CountVectorizer(ngram_range=n_grams, stop_words="english")
X_events = events_vectorizer.fit_transform(feedback_df_by_event["text"])
events_ngrams = events_vectorizer.get_feature_names_out()

# Generate n-gram frequencies
events_ngram_frequencies = dict(zip(events_ngrams, X_events.toarray().sum(axis=0)))

# Generate the word cloud
events_wordcloud = WordCloud(width=600, height=470, background_color=bg_color).generate_from_frequencies(events_ngram_frequencies)

events_ngrams_fig, events_ax = plt.subplots(figsize=(10, 5))
events_ax.imshow(events_wordcloud, interpolation="bilinear")
events_ax.axis("off")


# Display Visuals:
st.subheader("Complaints Info")
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

st.markdown("---")

st.subheader("Events Info")
third_first_col, third_second_col, third_third_col = st.columns(3)
with third_first_col:
    st.plotly_chart(sentiment_pie_chart)
with third_second_col:
    st.pyplot(events_ngrams_fig)
with third_third_col:
    # searchable dataframe for event reviews
    search_term = st.text_input("Search reviews:", "").split(" ")

    # Filter DataFrame based on search term
    if search_term:
        filtered_df = feedback_df_by_event[feedback_df_by_event["text"].apply(lambda x: all(term.lower() in str(x).lower() for term in search_term))]
    else:
        filtered_df = feedback_df_by_event

    # Display the filtered DataFrame
    display_df = pd.DataFrame(filtered_df.head(5)["text"].tolist(), columns=["Reviews"])
    st.dataframe(display_df.style.hide(axis="index"))