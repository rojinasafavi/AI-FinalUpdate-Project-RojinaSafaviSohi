import streamlit as st
import asyncio
import json
import pandas as pd
from io import StringIO
import time

from services.data_processing import normalize_text
from models.schemas import SocialMediaIngestion
from pydantic import ValidationError
from services.analysis_aggregator import aggregate_social_media_data
from services.report_generator import generate_management_report

# Configure a clean and professional page layout
st.set_page_config(page_title="Social Media Analytics", page_icon="📊", layout="wide")

st.title("📊 Social Media Analytics Dashboard")
st.markdown("Upload your structured JSON data to instantly generate executive business reports and insights.")

st.sidebar.header("⚙️ Configuration")
max_workers = st.sidebar.slider(
    "Parallel API Workers",
    min_value=1, max_value=20, value=10,
                help="Higher values process data faster but may hit Gemini rate limits."
)

uploaded_file = st.file_uploader("📂 Upload Social Media JSON File", type=["json"])

def process_uploaded_file(file_content: str):
    """Parses JSON content directly from Streamlit upload."""
    try:
        raw_data = json.loads(file_content)
        validated_data = SocialMediaIngestion(**raw_data)
        
        clean_texts = []
        for post in validated_data.posts:
            cleaned = normalize_text(post.text)
            if cleaned:
                clean_texts.append(cleaned)
                
        return clean_texts
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON Syntax: {e}")
        return None
    except ValidationError as e:
        st.error(f"Schema Validation Error: {e}")
        return None

if uploaded_file is not None:
    # Read the file content as a string
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    file_content = stringio.read()
    
    with st.spinner("Processing and Validating Data..."):
        clean_texts = process_uploaded_file(file_content)
        
    if clean_texts:
        st.success(f"Successfully loaded and cleaned {len(clean_texts)} valid posts.")
        
        if st.button("🚀 Generate Executive Analysis", type="primary"):
            
            with st.spinner("Analyzing Sentiments & Topics with Google Gemini... (This may take a minute)"):
                start_time = time.time()
                # Run the async aggregator safely inside the Streamlit sync execution flow
                aggregated_data = asyncio.run(aggregate_social_media_data(clean_texts, max_concurrent=max_workers))
                elapsed_time = time.time() - start_time
                
            if "error" in aggregated_data:
                st.error(f"Analysis failed: {aggregated_data['error']}")
            else:
                st.info(f"Analysis completed in {elapsed_time:.2f} seconds.")
                
                # --- Visualizations ---
                st.markdown("---")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("Sentiment Distribution 🎭")
                    sentiment_dist = aggregated_data.get("sentiment_distribution", {})
                    if sentiment_dist:
                        # Convert data dict into a DataFrame for the bar chart
                        df_sentiment = pd.DataFrame(
                            list(sentiment_dist.values()),
                            index=list(sentiment_dist.keys()),
                            columns=["Percentage (%)"]
                        )
                        st.bar_chart(df_sentiment, color="#5B8FF9")
                    else:
                        st.write("No sentiment data available.")

                with col2:
                    st.subheader("Top Topics 📌")
                    topics = aggregated_data.get("common_topics", [])
                    if topics:
                        # Convert the topic array into an indexed DataFrame
                        df_topics = pd.DataFrame(topics)
                        df_topics.set_index("topic", inplace=True)
                        st.bar_chart(df_topics, color="#5AD8A6", y="count")
                    else:
                        st.write("No topics extracted.")

                st.markdown("---")
                
                # --- Management Report ---
                with st.spinner("Synthesizing Executive Report..."):
                    final_report = asyncio.run(generate_management_report(aggregated_data))
                    
                st.subheader("Strategic Management Report 📑")
                st.markdown(final_report)
                
                # Provide a convenient download button
                st.download_button(
                    label="💾 Download Report as Markdown",
                    data=final_report,
                    file_name="management_report.md",
                    mime="text/markdown",
                )
