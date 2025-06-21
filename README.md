# 📰 AI News Summarizer

A Python-based intelligent news briefing tool that fetches real-time articles from **trusted sources**, summarizes them into **news**, **podcast scripts**, or **debate transcripts**, and follows principles of responsible journalism.

## 🚀 Features

- 🔎 Live news fetching via RSS & Google Search from **trusted sources** (NDTV, BBC, TOI, etc.)
- 🌐 Headless browser scraping using **Playwright**
- 🧠 Natural summarization using **open-source LLMs** (supports Hugging Face or Groq APIs)
- 🎙️ Multiple output formats: News, Podcast, or Debate
- ⚖️ Upholds journalism principles: **truth**, **clarity**, **objectivity**, and **transparency**
- ⏱️ Custom briefing durations: 1, 3, 5, or 10 minutes
- 🔐 API key management via `.env` file (e.g., ElevenLabs, Groq)

## 🛠️ Setup Instructions

```bash
# 1. Clone the Repository
git clone https://github.com/your-username/news-summarizer.git
cd news-summarizer

# 2. Install Requirements
pip install -r requirements.txt
playwright install chromium

# 3. Create a .env file with your API keys
echo "GROQ_API_TOKEN=your_groq_api_key" >> .env
echo "ELEVENLABS_API_KEY=your_elevenlabs_key" >> .env

# 4. Run the app
python main.py

📜 License
This project is for educational and research purposes only. Use responsibly.

🙋‍♂️ Author
Built with ❤️ by Manas Kumar Sinha
```
