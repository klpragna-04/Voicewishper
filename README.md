# Voicewishper
# VoiceWhisper: Enhanced Multilingual AI Conversation Assistant

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.7%2B-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

## 🌟 Overview

VoiceWhisper is a real-time, multilingual voice conversation interface that connects users with AI through natural speech. This application enables fluid, engaging conversations in multiple languages with high-quality voice synthesis and intelligent responses.

## ✨ Features

- **Multilingual Support**: Converse fluently in English, Hindi, and Telugu
- **High-Quality Voice Synthesis**: Premium text-to-speech using ElevenLabs API with fallback to Google TTS
- **Intelligent Responses**: Powered by Google's Gemini AI for context-aware conversations
- **Real-Time Transcription**: See your words as you speak them
- **API Key Rotation**: Automatic rotation between multiple ElevenLabs API keys for uninterrupted usage
- **Graceful Degradation**: Fallback mechanisms ensure conversation continues even if services are unavailable

## 🛠️ Technologies

- **AI & Natural Language Processing**
  - Google Gemini API (via `google.generativeai`)
  - Speech Recognition (`speech_recognition`)

- **Text-to-Speech**
  - ElevenLabs API (premium voice synthesis)
  - Google Text-to-Speech (`gtts` library)

- **Audio Processing**
  - PyGame for audio playback and management

- **Core Technologies**
  - Python 3.7+
  - Multithreading for concurrent processing
  - Queue-based real-time transcription processing

## 📋 Prerequisites

- Python 3.7 or higher
- Internet connection
- Microphone for voice input
- Speakers for audio output
- API keys:
  - Google Gemini API key
  - ElevenLabs API key(s)

## 🔧 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voicewhisper.git
   cd voicewhisper
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your API keys:
   - Replace the placeholder API keys in the script with your own:
     - `GEMINI_API_KEY`: Your Google Gemini API key
     - `ELEVEN_LABS_API_KEYS`: List of your ElevenLabs API keys

## 🚀 Usage

Run the application:
```bash
python voicewhisper.py
```

The program will prompt you to:
1. Select your preferred language (English, Hindi, or Telugu)
2. Choose your speech synthesis method (ElevenLabs or Google TTS)

Once started, simply speak naturally and the AI will respond. You can end the conversation at any time by saying "goodbye" in your selected language or by pressing Ctrl+C.

## 🔄 Conversation Flow

1. The program greets you in your selected language
2. You speak (real-time transcription appears on screen)
3. Your complete statement is processed once you pause speaking
4. AI generates an appropriate response
5. Response is spoken aloud using the selected voice synthesis method
6. Conversation continues until you say "goodbye" or another exit command

## 🌐 Language Support

- **English** (`en-US`): Full support with dedicated voices
- **Hindi** (`hi-IN`): Native language support with dedicated voice
- **Telugu** (`te-IN`): Native language support with dedicated voice

## ⚙️ Configuration Options

Edit the script to customize:
- Voice IDs for different languages
- System prompts for AI conversation style
- Speech recognition parameters
- Exit command phrases for each language

## 📝 Notes

- The ElevenLabs API has usage limits. Multiple API keys are used with automatic rotation to maximize available usage.
- Google TTS serves as a fallback if all ElevenLabs keys reach their quota limits.
- Ambient noise calibration happens at startup to improve speech recognition accuracy.






