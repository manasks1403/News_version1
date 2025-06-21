import streamlit as st
import asyncio
import nest_asyncio
from main import AudioOptimizedNewsAggregator, ElevenLabsAudioGenerator
import os
import io
import tempfile

# Apply nest_asyncio to handle asyncio in Streamlit
nest_asyncio.apply()

st.set_page_config(
    page_title="Audio News Aggregator", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🎙️ Integrated Audio News Aggregator")

# Initialize session state
if 'result' not in st.session_state:
    st.session_state.result = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# API Keys from Streamlit secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    ELEVENLABS_API_KEY = st.secrets["ELEVENLABS_API_KEY"]
except KeyError:
    st.error("❌ API keys not found in Streamlit secrets. Please add GROQ_API_KEY and ELEVENLABS_API_KEY to your secrets.")
    st.stop()

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

# Convert format choice to match main.py expectations
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
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize classes
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
        
        st.success(f"✅ Found {len(urls)} relevant sources")
        
        # Fetch articles
        status_text.text("📄 Fetching article content...")
        progress_bar.progress(40)
        
        # Run the async function
        articles = asyncio.run(aggregator.fetch_all_articles(urls))
        
        if not articles:
            st.error("❌ Could not fetch content from any sources. Please try again later.")
            st.session_state.processing = False
            st.stop()
        
        st.success(f"✅ Successfully processed {len(articles)} articles")
        
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
        
        # Save script to temporary file
        script_filename = f"{topic.replace(' ', '_')}_{preferences['format']}_script.txt"
        
        # Generate audio
        status_text.text("🎙️ Converting script to audio...")
        progress_bar.progress(80)
        
        audio_result = audio_gen.generate_audio_from_script(
            script, 
            preferences['format'], 
            topic
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Complete!")
        
        # Store results in session state
        st.session_state.result = {
            "script": script,
            "script_filename": script_filename,
            "audio_result": audio_result,
            "topic": topic,
            "format": format_choice,
            "duration": duration,
            "articles_count": len(articles),
            "sources": [article.get('url', 'Unknown') for article in articles[:5]]  # Show first 5 sources
        }
        
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.session_state.processing = False

# Display results
if st.session_state.result:
    result = st.session_state.result
    
    st.success("🎉 Audio briefing generated successfully!")
    
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
            help="This is the generated script that was converted to audio"
        )
        
        # Download script button
        st.download_button(
            label="📥 Download Script",
            data=result["script"],
            file_name=result["script_filename"],
            mime="text/plain"
        )
    
    # Audio section
    st.subheader("🎧 Generated Audio")
    
    if isinstance(result["audio_result"], str) and result["audio_result"].endswith(".mp3"):
        # Single audio file
        try:
            with open(result["audio_result"], "rb") as audio_file:
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3")
                
                # Download button for audio
                st.download_button(
                    label="📥 Download Audio",
                    data=audio_bytes,
                    file_name=result["audio_result"],
                    mime="audio/mp3"
                )
        except FileNotFoundError:
            st.error("❌ Audio file not found")
    
    elif isinstance(result["audio_result"], list):
        # Multiple audio segments
        st.info(f"Generated {len(result['audio_result'])} audio segments:")
        
        for i, audio_file in enumerate(result["audio_result"], 1):
            st.write(f"**Segment {i}:**")
            try:
                with open(audio_file, "rb") as f:
                    audio_bytes = f.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    
                    # Download button for each segment
                    st.download_button(
                        label=f"📥 Download Segment {i}",
                        data=audio_bytes,
                        file_name=audio_file,
                        mime="audio/mp3",
                        key=f"download_segment_{i}"
                    )
            except FileNotFoundError:
                st.error(f"❌ Audio segment {i} not found")
    
    else:
        st.warning("⚠️ Audio generation completed but files may not be accessible")
    
    # Sources used
    with st.expander("📰 News Sources Used"):
        for i, source in enumerate(result["sources"], 1):
            st.write(f"{i}. {source}")
    
    # Reset button
    if st.button("🔄 Generate Another Briefing"):
        st.session_state.result = None
        st.session_state.processing = False
        st.rerun()

# Instructions
with st.sidebar:
    st.header("📋 How to Use")
    st.write("""
    1. **Enter Topic**: Type any news topic you're interested in
    2. **Choose Format**: 
       - **News**: Professional broadcast style
       - **Podcast**: Conversational discussion
       - **Debate**: Multiple perspectives
    3. **Select Duration**: 1-10 minutes
    4. **Generate**: Click the button and wait
    5. **Listen & Download**: Play the audio and download files
    """)
    
    st.header("🔧 Features")
    st.write("""
    - Fetches from trusted Indian & international news sources
    - AI-powered script generation
    - Multi-voice audio synthesis
    - Download scripts and audio files
    """)
    
    st.header("⚡ Tips")
    st.write("""
    - Be specific with your topic (e.g., "India budget 2025" vs "budget")
    - Longer durations provide more detailed coverage
    - Podcast format works well for complex topics
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🎙️ Powered by Groq LLaMA & ElevenLabs | Built with Streamlit"
    "</div>", 
    unsafe_allow_html=True
)