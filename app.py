import streamlit as st
from main import AudioOptimizedNewsAggregator, ElevenLabsAudioGenerator
from io import BytesIO
import time
import os

# Set page config
st.set_page_config(
    page_title="Audio News Aggregator", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .stTextInput input {
        font-size: 18px !important;
    }
    .stSelectbox select {
        font-size: 16px !important;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 10px 24px;
        border-radius: 5px;
        border: none;
    }
    .stButton button:hover {
        background-color: #45a049;
    }
    .stDownloadButton button {
        background-color: #2196F3 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'result' not in st.session_state:
    st.session_state.result = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Get API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Check if API keys are available
if not GROQ_API_KEY or not ELEVENLABS_API_KEY:
    st.error("❌ API keys not found. Please set GROQ_API_KEY and ELEVENLABS_API_KEY environment variables.")
    st.stop()

# Main app
st.title("🎙️ Integrated Audio News Aggregator")
st.markdown("---")

# Input form
with st.form("news_form"):
    topic = st.text_input(
        "📌 Enter a news topic", 
        placeholder="e.g., Indian elections 2025",
        help="Enter any news topic you want to create an audio briefing for"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        format_choice = st.selectbox(
            "🎯 Select Format", 
            ["News", "Podcast", "Debate"],
            index=0,
            help="Choose the style of your audio briefing"
        )
    
    with col2:
        duration = st.select_slider(
            "⏱️ Duration (minutes)", 
            options=[1, 3, 5, 10],
            value=3,
            help="Select how long you want the audio to be"
        )
    
    submit = st.form_submit_button("🚀 Generate Audio Briefing", use_container_width=True)

# Convert format choice
format_map = {"News": "news", "Podcast": "podcast", "Debate": "debate"}

if submit and topic:
    st.session_state.processing = True
    st.session_state.result = None
    
    # Create preferences object
    preferences = {
        "format": format_map[format_choice],
        "duration_minutes": duration,
        "word_limit": duration * 150
    }
    
    # Initialize progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize components
        status_text.text("🔧 Initializing components...")
        progress_bar.progress(10)
        
        aggregator = AudioOptimizedNewsAggregator(groq_api_key=GROQ_API_KEY)
        audio_gen = ElevenLabsAudioGenerator(ELEVENLABS_API_KEY)
        
        # Fetch URLs
        status_text.text(f"🔍 Searching for '{topic}' articles...")
        progress_bar.progress(20)
        
        urls = aggregator.get_combined_urls(topic, max_results=10)
        if not urls:
            st.error("❌ No trusted news sources found for this topic. Try a different search term.")
            st.session_state.processing = False
            st.stop()
        
        # Fetch articles
        status_text.text("📄 Fetching article content...")
        progress_bar.progress(40)
        
        articles = aggregator.fetch_all_articles(urls)
        
        if not articles:
            st.error("❌ Could not fetch content from any sources. Please try again later.")
            st.session_state.processing = False
            st.stop()
        
        # Generate script
        status_text.text("🤖 Generating audio-optimized script...")
        progress_bar.progress(60)
        
        combined_text = aggregator.combine_articles_text(articles)
        prompt = aggregator.get_audio_optimized_prompts(topic, preferences)
        script = aggregator.call_groq_api(prompt, combined_text)
        
        if script.startswith("Error:"):
            st.error(f"❌ Script generation failed: {script}")
            st.session_state.processing = False
            st.stop()
        
        # Generate audio
        status_text.text("🎙️ Converting script to audio...")
        progress_bar.progress(80)
        
        audio_result = audio_gen.generate_audio_from_script(script, preferences['format'], topic)
        
        progress_bar.progress(100)
        status_text.text("✅ Complete!")
        
        # Store results
        st.session_state.result = {
            "script": script,
            "audio_result": audio_result,
            "topic": topic,
            "format": format_choice,
            "duration": duration,
            "articles_count": len(articles),
            "sources": [article.get('url', 'Unknown') for article in articles[:5]]
        }
        
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.session_state.processing = False

# Display results
if st.session_state.result:
    result = st.session_state.result
    
    st.success("🎉 Audio briefing generated successfully!")
    st.balloons()
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Format", result["format"])
    with col2:
        st.metric("Duration", f"{result['duration']} min")
    with col3:
        st.metric("Sources Used", result["articles_count"])
    
    # Script section
    with st.expander("📄 View Generated Script", expanded=True):
        st.text_area(
            "Script Content", 
            result["script"], 
            height=300,
            help="This is the generated script that was converted to audio",
            label_visibility="collapsed"
        )
        
        # Download script button
        st.download_button(
            label="📥 Download Script",
            data=result["script"],
            file_name=f"{result['topic'].replace(' ', '_')}_{result['format']}_script.txt",
            mime="text/plain"
        )
    
    # Audio section
    st.subheader("🎧 Generated Audio")
    
    if result["audio_result"]:
        audio_bytes = result["audio_result"].read()
        st.audio(audio_bytes, format="audio/mp3")
        
        # Download button for audio
        st.download_button(
            label="📥 Download Audio",
            data=audio_bytes,
            file_name=f"{result['topic'].replace(' ', '_')}_{result['format']}_audio.mp3",
            mime="audio/mp3"
        )
    else:
        st.error("❌ Audio generation failed")
    
    # Sources used
    with st.expander("📰 News Sources Used"):
        for i, source in enumerate(result["sources"], 1):
            st.write(f"{i}. {source}")
    
    # Reset button
    if st.button("🔄 Generate Another Briefing"):
        st.session_state.result = None
        st.session_state.processing = False
        st.rerun()

# Sidebar with instructions
with st.sidebar:
    st.header("📋 How to Use")
    st.markdown("""
    1. **Enter Topic**: Type any news topic
    2. **Choose Format**: 
       - **News**: Professional broadcast
       - **Podcast**: Conversational
       - **Debate**: Multiple perspectives
    3. **Select Duration**: 1-10 minutes
    4. **Generate**: Click the button
    5. **Listen & Download**: Enjoy your briefing
    """)
    
    st.header("🔧 Features")
    st.markdown("""
    - Trusted news sources
    - AI-powered script generation
    - High-quality voice synthesis
    - Multiple output formats
    """)
    
    st.header("⚡ Tips")
    st.markdown("""
    - Be specific with topics
    - Longer durations = more detail
    - Podcast format for complex topics
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🎙️ Powered by Groq LLaMA & ElevenLabs | Built with Streamlit"
    "</div>", 
    unsafe_allow_html=True
)