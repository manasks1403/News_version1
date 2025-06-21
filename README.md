# 🎙️ Integrated Audio News Aggregator

![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)

A Python application that fetches news articles, generates audio-optimized scripts, and converts them into high-quality spoken briefings using AI.

## ✨ Key Features

1. **Smart News Aggregation** - Fetches latest articles from 15+ trusted sources like BBC, Reuters, and The Hindu

2. **AI-Powered Scriptwriting** - Uses Groq's Llama 3 to generate natural-sounding scripts optimized for audio

3. **Interactive Web App** - Streamlit interface with intuitive controls:

   - Topic search bar
   - Format selector (News/Podcast/Debate)
   - Duration slider (1-10 minutes)
   - Generate button

4. **Multi-Voice Audio** - Professional TTS with ElevenLabs:

   - News: Single authoritative voice
   - Podcast: Two conversational hosts
   - Debate: Moderator + 2 speakers

5. **Live Audio Player** - Built-in audio widget to:

   - Play/pause generated briefings
   - Adjust volume
   - See playback progress

6. **Download Options** - Save outputs as:

   - MP3 audio files (128kbps)
   - Text transcripts (TXT)

7. **Customizable Length** - Precision duration control:

   - 1-min (quick updates)
   - 3-min (standard reports)
   - 5-10 min (detailed analysis)

8. **Audio Optimization** - Automatic:

   - Pause insertion
   - Volume normalization
   - Pronunciation guides

9. **Source Attribution** - Includes references to original articles

10. **Mobile-Friendly** - Works on both desktop and mobile browsers

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Streamlit
- API keys for [Groq](https://groq.com/) & [ElevenLabs](https://elevenlabs.io/)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/audio-news-aggregator.git
cd audio-news-aggregator
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a .env file:

```bash
echo "GROQ_API_KEY=your_groq_api_key" > .env
echo "ELEVENLABS_API_KEY=your_elevenlabs_api_key" >> .env
```

4. Run the app:

```bash
streamlit run app.py
```

## ✨ How It Works

- News Collection
- Searches multiple trusted news sources
- Combines and filters relevant articles
- Script Generation
- Processes content with Groq's AI
- Creates audio-optimized scripts with proper pacing
- Audio Production
- Converts text to speech using ElevenLabs
- Supports multi-speaker formats

## 📜 License

MIT License - See LICENSE for details.

## 💡 Support

For help or feature requests, please open an issue.
