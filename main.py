# INTEGRATED AUDIO NEWS AGGREGATOR
# =================================
# API KEYS CONFIGURATION
from dotenv import load_dotenv
load_dotenv()

import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
# =================================

# =================================
# Main Code - Do not modify below
# =================================

import newspaper
import feedparser
from googlesearch import search
from bs4 import BeautifulSoup
from newspaper import Article
import requests
import json
import re
import os
from pathlib import Path
import time
import glob
from io import BytesIO


class AudioOptimizedNewsAggregator:
    def __init__(self, groq_api_key=None):
        self.trusted_domains = [
            "ndtv.com", "indiatoday.in", "indianexpress.com", "hindustantimes.com",
            "timesofindia.indiatimes.com", "thehindu.com", "theprint.in", "scroll.in",
            "thewire.in", "bbc.com", "reuters.com", "economictimes.indiatimes.com",
            "theguardian.com", "nytimes.com"
        ]
        self.groq_api_key = groq_api_key
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        
    def is_trusted_url(self, url):
        """Check if URL belongs to a trusted domain."""
        return any(domain in url for domain in self.trusted_domains)
    
    def get_rss_urls(self, topic, max_results=10):
        """Fetch news URLs using Google News RSS feed."""
        query = topic.replace(" ", "+")
        rss_url = f"https://news.google.com/rss/search?q={query}"
        feed = feedparser.parse(rss_url)
        
        articles = []
        for entry in feed.entries[:max_results]:
            if self.is_trusted_url(entry.link):
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published
                })
        return articles
    
    def get_google_search_urls(self, topic, max_results=10):
        """Fetch news URLs using Google Search."""
        query = f"{topic} site:" + " OR site:".join(self.trusted_domains)
        results = []
        try:
            for url in search(query, num_results=max_results, lang="en"):
                if self.is_trusted_url(url):
                    results.append(url)
        except Exception:
            pass  # Silently handle search errors
        return results
    
    def get_combined_urls(self, topic, max_results=10):
        """Combine results from RSS and Google, remove duplicates."""
        rss_articles = self.get_rss_urls(topic, max_results)
        rss_urls = [a["link"] for a in rss_articles]
        google_urls = self.get_google_search_urls(topic, max_results)
        
        # Combine and deduplicate
        all_urls = list(set(rss_urls + google_urls))
        return all_urls[:max_results]
    
    def fetch_article_content(self, url):
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return {
                "title": article.title or "Untitled",
                "text": article.text.strip() if article.text else None,
                "url": url
            }
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return {"title": None, "text": None, "url": url}
    
    def fetch_all_articles(self, urls):
        """Fetch all articles synchronously."""
        print(f"🔄 Fetching content from {len(urls)} sources...")
        
        results = []
        for url in urls:
            result = self.fetch_article_content(url)
            if result["text"]:
                results.append(result)
            time.sleep(1)  # Rate limiting
        
        print(f"✅ Successfully fetched {len(results)} articles")
        return results
    
    def get_audio_optimized_prompts(self, topic, preferences):
        """Generate audio-optimized prompts for better TTS conversion."""
        format_type = preferences['format']
        word_limit = preferences['word_limit']
        duration = preferences['duration_minutes']
        
        prompts = {
            "news": f"""Create a professional news broadcast script about "{topic}" optimized for text-to-speech conversion.

AUDIO REQUIREMENTS:
- Write exactly {word_limit} words
- Use natural, conversational sentence structure
- Include pronunciation guides for difficult names/terms in brackets [like this]
- Add natural pauses with commas and periods
- Avoid complex punctuation that confuses TTS
- Use "and" instead of "&" symbols

STRUCTURE:
1. Opening: "Good morning, this is your news update on {topic}"
2. Lead story with key facts
3. Supporting details and context  
4. Impact and implications
5. Closing: "That's your update on {topic}. Thank you for listening."

STYLE:
- Clear, authoritative tone
- Short to medium sentences (10-20 words)
- Active voice throughout
- Specific numbers and dates
- Natural broadcast language

Write the complete broadcast script now.""",

            "podcast": f"""Create a {duration}-minute podcast conversation script about "{topic}" optimized for multi-voice text-to-speech.

AUDIO REQUIREMENTS:
- Label each speaker clearly (HOST 1:, HOST 2:, etc.)
- Write natural dialogue (~{word_limit} words total)
- Include conversational fillers like "you know", "actually", "well"
- Use contractions (it's, we're, that's)
- Add natural pauses with ellipses...
- Pronunciation guides for difficult terms [like this]

STRUCTURE:
HOST 1: Welcome back to the show! Today we're diving into {topic}. 
HOST 2: That's right, and there's been some interesting developments...

[Continue with natural back-and-forth discussion]

DIALOGUE STYLE:
- Natural interruptions and agreement ("Exactly!", "Right")
- Questions to each other
- Personal reactions ("That's fascinating", "I had no idea")
- Smooth topic transitions
- Engaging, conversational tone

Create the complete dialogue script with clear speaker labels.""",

            "debate": f"""Create a structured debate script about "{topic}" with multiple speakers, optimized for text-to-speech conversion.

AUDIO REQUIREMENTS:
- Clear speaker labels (MODERATOR:, SPEAKER A:, SPEAKER B:)
- Approximately {word_limit} words total
- Natural debate language and timing
- Pronunciation guides [like this] for complex terms
- Clear transitions between speakers

STRUCTURE:
MODERATOR: Welcome to today's debate on {topic}. Let's hear different perspectives...

SPEAKER A: [Position 1 with evidence and reasoning]
SPEAKER B: [Counter-position with different evidence]  
MODERATOR: [Transitional questions and summaries]
SPEAKER A: [Response and additional points]
SPEAKER B: [Counter-response]
MODERATOR: [Final summary of key points from both sides]

STYLE:
- Respectful but passionate debate tone
- Clear argumentative structure
- Evidence-based reasoning
- Natural debate interruptions and responses
- Balanced time for each perspective

Write the complete debate script with clear speaker identification."""
        }
        
        return prompts.get(format_type, prompts["news"])
    
    def call_groq_api(self, prompt, context):
        """Call Groq API with updated model."""
        if not self.groq_api_key:
            return "Error: Groq API key not provided"
        
        print("🤖 Generating audio-optimized content with Llama 3.3 70B...")
        
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        # Combine context and prompt
        full_prompt = f"""Based on the following news articles, {prompt}

NEWS ARTICLES:
{context}

Generate the response now:"""
        
        # Check total length and truncate if needed
        max_total_chars = 45000  # Conservative limit
        if len(full_prompt) > max_total_chars:
            context_limit = max_total_chars - len(prompt) - 200
            context = context[:context_limit] + "\n[Content truncated]"
            full_prompt = f"""Based on the following news articles, {prompt}

NEWS ARTICLES:
{context}

Generate the response now:"""
        
        data = {
            "messages": [
                {
                    "role": "system", 
                    "content": "You are an expert audio content creator specializing in news broadcasting, podcast production, and debate moderation. Create scripts optimized for text-to-speech conversion with natural flow, clear speaker identification, and proper audio formatting."
                },
                {
                    "role": "user", 
                    "content": full_prompt
                }
            ],
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.4,  # Slightly higher for more natural dialogue
            "max_tokens": 2500,  # Increased for longer scripts
            "top_p": 0.9,
            "stream": False
        }
        
        try:
            response = requests.post(self.groq_url, headers=headers, json=data, timeout=60)
            
            if response.status_code != 200:
                return f"API Error {response.status_code}: {response.text}"
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            print("✅ Audio-optimized content generated successfully!")
            return content
            
        except requests.exceptions.Timeout:
            return "Error: API request timed out"
        except requests.exceptions.RequestException as e:
            return f"Network Error: {str(e)}"
        except KeyError as e:
            return f"Response Format Error: {str(e)}"
        except Exception as e:
            return f"Unexpected Error: {str(e)}"
    
    def combine_articles_text(self, articles):
        """Combine all article content into one text."""
        combined_text = ""
        for article in articles:
            if article["title"] and article["text"]:
                combined_text += f"TITLE: {article['title']}\n"
                combined_text += f"CONTENT: {article['text'][:2000]}\n"
                combined_text += f"SOURCE: {article['url']}\n"
                combined_text += "---\n"
        return combined_text.strip()
    
    def save_audio_script(self, content, topic, format_type):
        """Save the audio script to a file."""
        filename = f"{topic.replace(' ', '_')}_{format_type}_script.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return filename
        except Exception as e:
            print(f"❌ Could not save file: {e}")
            return None
    
    def generate_audio_ready_briefing(self, topic, preferences):
        """Main function to generate audio-ready news briefing."""
        # Fetch URLs
        print(f"🔍 Searching for '{topic}' articles...")
        urls = self.get_combined_urls(topic, max_results=15)
        if not urls:
            return None, "No trusted news sources found for this topic."
        
        # Fetch articles
        articles = self.fetch_all_articles(urls)
        if not articles:
            return None, "Could not fetch content from any sources."
        
        # Combine text
        print("📄 Processing article content...")
        combined_news = self.combine_articles_text(articles)
        
        # Limit context
        max_context_chars = 35000
        if len(combined_news) > max_context_chars:
            combined_news = combined_news[:max_context_chars] + "\n[Content truncated due to length]"
        
        # Generate audio-optimized prompt
        prompt = self.get_audio_optimized_prompts(topic, preferences)
        
        # Generate script using Groq
        script = self.call_groq_api(prompt, combined_news)
        
        # Save script to file
        filename = self.save_audio_script(script, topic, preferences['format'])
        
        return {
            "topic": topic,
            "preferences": preferences,
            "articles_count": len(articles),
            "generated_script": script,
            "script_file": filename,
            "sources_used": [article['url'] for article in articles]
        }, None


class ElevenLabsAudioGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        # Indian English voices optimized for clarity
        self.indian_voices = {
            "news": {
                "voice_id": "mCQMfsqGDT6IDkEKR20a",  # Adam - Clear, professional
                "name": "Jeevan"
            },
            "podcast_host1": {
                "voice_id": "mCQMfsqGDT6IDkEKR20a",  
                "name": "Jeevan"
            },
            "podcast_host2": {
                "voice_id": "0ZOhGcBopt9S6GBK8tnj",  # Domi - Engaging
                "name": "Ayesha"
            },
            "debate_moderator": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella - Authoritative
                "name": "Bella"
            },
            "debate_speaker_a": {
                "voice_id": "mCQMfsqGDT6IDkEKR20a",  # Antoni - Confident
                "name": "jeevan"
            },
            "debate_speaker_b": {
                "voice_id": "0ZOhGcBopt9S6GBK8tnj",  # Josh - Analytical
                "name": "Ayesha"
            }
        }
    
    def parse_script_by_format(self, script, format_type):
        """Parse script based on format to identify speakers."""
        if format_type == "news":
            return [{"speaker": "news", "text": script.strip()}]
        
        elif format_type == "podcast":
            segments = []
            
            # Handle inline HOST format - your actual format
            # Pattern to match HOST X: followed by text until next HOST or end
            pattern = r'HOST\s*(\d+)\s*:\s*(.*?)(?=\s*HOST\s*\d+\s*:|$)'
            matches = re.findall(pattern, script, re.DOTALL | re.IGNORECASE)
            
            for host_num, text in matches:
                text = text.strip()
                if text:  # Only add non-empty segments
                    speaker = "podcast_host1" if host_num == "1" else "podcast_host2"
                    segments.append({"speaker": speaker, "text": text})
            
            # If regex worked, return the segments
            if segments:
                return segments
            
            # Fallback 1: Split on HOST patterns and process sequentially
            parts = re.split(r'(\s*HOST\s*\d+\s*:\s*)', script, flags=re.IGNORECASE)
            
            current_speaker = None
            current_text = ""
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Check if this part is a HOST label
                host_match = re.match(r'HOST\s*(\d+)\s*:\s*', part, re.IGNORECASE)
                
                if host_match:
                    # Save previous segment if exists
                    if current_speaker and current_text.strip():
                        segments.append({"speaker": current_speaker, "text": current_text.strip()})
                    
                    # Start new segment
                    host_num = host_match.group(1)
                    current_speaker = "podcast_host1" if host_num == "1" else "podcast_host2"
                    current_text = ""
                else:
                    # This is content text
                    current_text += " " + part
            
            # Add final segment
            if current_speaker and current_text.strip():
                segments.append({"speaker": current_speaker, "text": current_text.strip()})
            
            # If we have segments now, return them
            if segments:
                return segments
            
            # Fallback 2: Manual character-by-character parsing for your exact format
            # Find all HOST positions
            host_positions = []
            for match in re.finditer(r'HOST\s*(\d+)\s*:', script, re.IGNORECASE):
                host_positions.append({
                    'pos': match.start(),
                    'end': match.end(),
                    'host_num': match.group(1),
                    'match': match.group(0)
                })
            
            # Extract text between HOST labels
            for i, host_info in enumerate(host_positions):
                start_pos = host_info['end']  # Start after "HOST X:"
                
                # Find end position (next HOST or end of script)
                if i + 1 < len(host_positions):
                    end_pos = host_positions[i + 1]['pos']
                else:
                    end_pos = len(script)
                
                # Extract text
                text = script[start_pos:end_pos].strip()
                
                if text:
                    speaker = "podcast_host1" if host_info['host_num'] == "1" else "podcast_host2"
                    segments.append({"speaker": speaker, "text": text})
            
            # Final fallback: Split script in half if still no segments
            if not segments:
                mid_point = len(script) // 2
                first_half = script[:mid_point].strip()
                second_half = script[mid_point:].strip()
                
                if first_half:
                    segments.append({"speaker": "podcast_host1", "text": first_half})
                if second_half:
                    segments.append({"speaker": "podcast_host2", "text": second_half})
            
            return segments
        
        elif format_type == "debate":
            segments = []
            
            # Split by speaker labels
            parts = re.split(r'(MODERATOR:|SPEAKER [AB]:)', script)
            
            current_speaker = None
            current_text = ""
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                if part == "MODERATOR:":
                    if current_speaker and current_text.strip():
                        segments.append({"speaker": current_speaker, "text": current_text.strip()})
                    current_speaker = "debate_moderator"
                    current_text = ""
                elif part == "SPEAKER A:":
                    if current_speaker and current_text.strip():
                        segments.append({"speaker": current_speaker, "text": current_text.strip()})
                    current_speaker = "debate_speaker_a"
                    current_text = ""
                elif part == "SPEAKER B:":
                    if current_speaker and current_text.strip():
                        segments.append({"speaker": current_speaker, "text": current_text.strip()})
                    current_speaker = "debate_speaker_b"
                    current_text = ""
                else:
                    current_text += " " + part
            
            # Add final segment
            if current_speaker and current_text.strip():
                segments.append({"speaker": current_speaker, "text": current_text.strip()})
            
            # Alternative parsing if no segments found
            if not segments:
                patterns = {
                    r'MODERATOR: (.*?)(?=SPEAKER [AB]:|$)': "debate_moderator",
                    r'SPEAKER A: (.*?)(?=SPEAKER B:|MODERATOR:|$)': "debate_speaker_a",
                    r'SPEAKER B: (.*?)(?=SPEAKER A:|MODERATOR:|$)': "debate_speaker_b"
                }
                
                for pattern, speaker in patterns.items():
                    matches = re.findall(pattern, script, re.DOTALL)
                    for match in matches:
                        segments.append({"speaker": speaker, "text": match.strip()})
            
            return segments
        
        return [{"speaker": "news", "text": script.strip()}]
    
    def clean_text_for_tts(self, text):
        """Clean text for better TTS conversion."""
        # Remove speaker labels that might have been missed
        text = re.sub(r'HOST\s*[12]\s*:\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'MODERATOR:\s*', '', text)
        text = re.sub(r'SPEAKER [AB]:\s*', '', text)
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\**', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)     # Remove italic
        text = re.sub(r'\[(.*?)\]', r'\1', text)     # Remove brackets, keep content
        text = ' '.join(text.split())                # Clean whitespace
        
        if not text.endswith(('.', '!', '?')):
            text += '.'
        
        return text
    
    def generate_speech(self, text, voice_id):
        """Generate speech using ElevenLabs API."""
        clean_text = self.clean_text_for_tts(text)
        
        tts_data = {
            "text": clean_text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": 0.2,
                "use_speaker_boost": True
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/text-to-speech/{voice_id}",
                json=tts_data,
                headers=self.headers,
                timeout=120
            )
            
            if response.status_code == 200:
                return BytesIO(response.content)
            else:
                print(f"❌ TTS Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ TTS Exception: {e}")
            return None
    
    def generate_audio_from_script(self, script_content, format_type, topic):
        """Generate audio from script."""
        print(f"🎙️ Converting {format_type} script to audio...")
        
        segments = self.parse_script_by_format(script_content, format_type)
        
        if not segments:
            print("❌ Could not parse script segments")
            return None
        
        print(f"📝 Found {len(segments)} speech segments")
        
        audio_segments = []
        
        for i, segment in enumerate(segments, 1):
            speaker = segment["speaker"]
            text = segment["text"]
            
            if not text.strip():
                continue
            
            voice_info = self.indian_voices.get(speaker, self.indian_voices["news"])
            voice_id = voice_info["voice_id"]
            voice_name = voice_info["name"]
            
            print(f"🔊 Generating segment {i}/{len(segments)}: {voice_name} ({speaker})")
            
            audio_data = self.generate_speech(text, voice_id)
            
            if audio_data:
                audio_segments.append(audio_data)
                print(f"✅ Generated segment {i}")
            else:
                print(f"❌ Failed to generate segment {i}")
            
            time.sleep(0.5)  # Respect API limits
        
        if not audio_segments:
            print("❌ No audio segments were generated")
            return None
        
        # Combine audio segments
        print(f"🔄 Combining {len(audio_segments)} audio segments...")
        
        try:
            from pydub import AudioSegment
            from pydub.effects import normalize
            
            combined = AudioSegment.empty()
            
            for audio_data in audio_segments:
                audio = AudioSegment.from_mp3(audio_data)
                combined += audio
                combined += AudioSegment.silent(duration=500)  # 0.5 second pause
            
            # Normalize audio
            combined = normalize(combined)
            
            # Create in-memory file
            output = BytesIO()
            combined.export(output, format="mp3")
            output.seek(0)
            
            print("✅ Audio generation complete!")
            return output
            
        except ImportError:
            print("⚠️ pydub not available, returning first segment only")
            if audio_segments:
                return audio_segments[0]
            return None
        
        except Exception as e:
            print(f"❌ Audio combination error: {e}")
            return None