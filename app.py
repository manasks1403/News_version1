import streamlit as st
import asyncio
from main import AudioOptimizedNewsAggregator, ElevenLabsAudioGenerator  # Assuming main.py contains your classes
from dotenv import load_dotenv
import os

# Load API keys from .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

st.set_page_config(page_title="Audio News Aggregator", layout="centered")

st.title("🎙️ Integrated Audio News Aggregator")

# Step 1: Get topic from user
topic = st.text_input("Enter a news topic", placeholder="e.g., Indian elections 2025")

# Step 2: Preferences
format_choice = st.selectbox("Select Format", ["News", "Podcast", "Debate"])
duration = st.select_slider("Select Duration (minutes)", options=[1, 3, 5, 10])

submit = st.button("Generate Audio Briefing")

# Convert format_choice to lowercase used in main.py
format_map = {"News": "news", "Podcast": "podcast", "Debate": "debate"}

if submit and topic:
    st.info(f"Processing topic: **{topic}**")

    preferences = {
        "format": format_map[format_choice],
        "duration_minutes": duration,
        "word_limit": duration * 150
    }

    aggregator = AudioOptimizedNewsAggregator(groq_api_key=GROQ_API_KEY)
    audio_gen = ElevenLabsAudioGenerator(ELEVENLABS_API_KEY)

    async def run_pipeline():
        urls = aggregator.get_combined_urls(topic)
        articles = await aggregator.fetch_all_articles(urls)
        if not articles:
            return None, "❌ Could not fetch articles"

        combined_text = aggregator.combine_articles_text(articles)
        prompt = aggregator.get_audio_optimized_prompts(topic, preferences)
        script = aggregator.call_groq_api(prompt, combined_text)

        filename = aggregator.save_audio_script(script, topic, preferences['format'])

        audio_path = audio_gen.generate_audio_from_script(script, preferences['format'], topic)

        return {
            "script": script,
            "filename": filename,
            "audio_path": audio_path
        }, None

    with st.spinner("Generating audio briefing..."):
        result, error = asyncio.run(run_pipeline())
    
    if error:
        st.error(error)
    else:
        st.success("Audio briefing generated successfully!")

        st.subheader("Generated Script")
        st.text_area("Script Output", result["script"], height=300)

        if isinstance(result["audio_path"], str) and result["audio_path"].endswith(".mp3"):
            st.audio(result["audio_path"], format="audio/mp3")

        elif isinstance(result["audio_path"], list):
            for file in result["audio_path"]:
                st.audio(file, format="audio/mp3")

else:
    st.caption("Enter a topic and click the button to start.")
