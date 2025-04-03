import speech_recognition as sr
import google.generativeai as genai
import requests
import io
import pygame
import time
from collections import deque
import threading
import sys
import os
import signal
import tempfile
import queue
import random

# API Key for Gemini
GEMINI_API_KEY = "AIzaSyBZCaesJALTDsRuLvgBU5a6RWaVcB5JEX8"

# ElevenLabs API Keys (Multiple keys for rotation)
ELEVEN_LABS_API_KEYS = [
    "sk_b0ab2cd5f72c8c7231adc0c98d1e0b4db93a8c8b2fac7d35",  # Original key
    "sk_1511f98c487320b1ce6da259246543c8a22a6cffa2cbe8f4",  # Add your second API key
    "sk_aa0d4cf1d05ab199ad77a78b803703e2d51a9dbc28d4b4fd"    # Add your third API key
]

# Current API key index
current_key_index = 0

# ElevenLabs Voice IDs for different languages
VOICE_IDS = {
    "en-US": "nPczCjzI2devNBz1zQrb",  # English voice
    "hi-IN": "pNInz6obpgDQGcFmaJgB",  # Hindi voice
    "te-IN": "XB0fDUnXU5powFXDhCwa"   # Telugu voice
}

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Initialize speech recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 350
recognizer.pause_threshold = 0.8  # Reduced for more responsive real-time
recognizer.dynamic_energy_threshold = True

# System prompts for natural conversation in different languages
SYSTEM_PROMPTS = {
    "en-US": "You are a friendly and supportive AI friend speaking in English. Keep responses brief, engaging and conversational. Respond directly to the user's questions and statements without translating or explaining what they said.",
    
    "hi-IN": "You are a friendly and supportive AI friend who speaks fluent Hindi. Keep responses brief, engaging and conversational in Hindi. The user is speaking to you in Hindi. Respond directly to the user's questions and statements in Hindi without translating or explaining what they said.",
    
    "te-IN": "You are a friendly and supportive AI friend who speaks fluent Telugu. Keep responses brief, engaging and conversational in Telugu. The user is speaking to you in Telugu. Respond directly to the user's questions and statements in Telugu without translating or explaining what they said."
}

# Store conversation history
conversation_history = deque(maxlen=25)

# Global variables
selected_language = "en-US"
exit_phrases = {
    "en-US": ["goodbye", "bye", "exit", "quit", "stop", "end", "terminate"],
    "hi-IN": ["अलविदा", "बाय", "टाटा", "खत्म", "बंद", "निकास"],
    "te-IN": ["వీడ్కోలు", "బై", "నిష్క్రమణ", "ముగించు", "ఆపు"]
}

# Define a threading event for safe thread termination
exit_event = threading.Event()

# Voice mode flag
use_voice = True
use_elevenlabs = True

# Queue for real-time transcription
transcription_queue = queue.Queue()

# Create a buffer for real-time transcriptions
transcription_buffer = ""

def get_next_api_key():
    """Rotate to the next API key"""
    global current_key_index
    current_key_index = (current_key_index + 1) % len(ELEVEN_LABS_API_KEYS)
    return ELEVEN_LABS_API_KEYS[current_key_index]

def check_internet_connection():
    """Check if internet connection is available"""
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except:
        return False

def end_program():
    """Safely end the program and all threads"""
    exit_event.set()
    print("\n🛑 Ending conversation and closing application...")
    time.sleep(1)  # Give threads time to clean up
    
    # Clean up any temporary files
    for file in os.listdir(tempfile.gettempdir()):
        if file.startswith('tts_') and file.endswith('.mp3'):
            try:
                os.remove(os.path.join(tempfile.gettempdir(), file))
            except:
                pass
    
    # If program hasn't exited yet, force exit
    os._exit(0)

def check_for_exit_command(text, language):
    """Check if the text contains any exit phrases in the given language"""
    if not text:
        return False
        
    text_lower = text.lower()
    
    # First check in the selected language
    for phrase in exit_phrases.get(language, []):
        if phrase.lower() in text_lower:
            return True
    
    # Also check English exit phrases as fallback for all languages
    if language != "en-US":
        for phrase in exit_phrases["en-US"]:
            if phrase.lower() in text_lower:
                return True
    
    return False

def get_ai_response(user_text, language="en-US"):
    """Get response from Gemini AI based on conversation history and language."""
    # Add user message to history
    conversation_history.append(f"User: {user_text}")
    
    try:
        # Get the appropriate system prompt for the language
        system_prompt = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en-US"])
        
        # For non-English languages, add instruction to respond in that language
        language_instruction = ""
        if language == "hi-IN":
            language_instruction = "Respond in Hindi. हिंदी में जवाब दें।"
        elif language == "te-IN":
            language_instruction = "Respond in Telugu. తెలుగులో సమాధానం ఇవ్వండి."
        
        # Prepare conversation with history as context
        # Include both the original text and the language instruction
        conversation_context = (
            f"{system_prompt}\n"
            f"{language_instruction}\n"
            f"The user is speaking in {language.split('-')[0]}.\n"
            f"\n".join(conversation_history)
        )

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(conversation_context)
        
        ai_reply = response.text
        
        # Store AI response in history - but don't include "AI:" prefix
        conversation_history.append(f"AI: {ai_reply}")

        return ai_reply
    except Exception as e:
        print(f"\n⚠️ AI Error: {str(e)}")
        if language == "hi-IN":
            return "मुझे जवाब देने में परेशानी हो रही है। कृपया फिर से कोशिश करें।"
        elif language == "te-IN":
            return "సమాధానం ఇవ్వడంలో నాకు సమస్య ఉంది. దయచేసి మళ్లీ ప్రయత్నించండి."
        else:
            return f"I'm having trouble connecting. Please try again."

def speak_with_elevenlabs(text, language="en-US"):
    """Convert text to speech using ElevenLabs API with language-specific voices."""
    global use_voice, use_elevenlabs
    
    if exit_event.is_set() or not use_voice or not use_elevenlabs:
        return False  # Don't speak if we're exiting or voice is disabled
    
    # Get the appropriate voice ID for the language
    voice_id = VOICE_IDS.get(language, VOICE_IDS["en-US"])
    
    # Get the current API key
    api_key = ELEVEN_LABS_API_KEYS[current_key_index]
        
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.7}
    }

    try:
        print(f"\n🔊 Speaking with ElevenLabs in {language.split('-')[0]}...")
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            audio_data = io.BytesIO(response.content)
            pygame.mixer.init()
            pygame.mixer.music.load(audio_data, "mp3")
            pygame.mixer.music.play()
            
            # Only wait for playback to finish if we're not exiting
            while pygame.mixer.music.get_busy() and not exit_event.is_set():
                time.sleep(0.1)
                
            # If we need to exit, stop playback immediately
            if exit_event.is_set() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            
            return True
        else:
            error_message = f"ElevenLabs Error: {response.status_code}"
            try:
                error_data = response.json()
                if "detail" in error_data and "status" in error_data["detail"]:
                    if error_data["detail"]["status"] == "quota_exceeded":
                        print(f"\n⚠️ ElevenLabs quota exceeded for key {current_key_index+1}. Trying next key...")
                        # Try with the next API key
                        next_key = get_next_api_key()
                        print(f"Switched to API key {current_key_index+1}")
                        # Try again with the new key
                        return speak_with_elevenlabs(text, language)
            except:
                pass
                
            print(f"\n⚠️ {error_message}")
            # Fall back to Google TTS if all ElevenLabs keys fail
            if current_key_index == len(ELEVEN_LABS_API_KEYS) - 1:
                print("\n⚠️ All ElevenLabs API keys have reached their quota. Switching to Google TTS.")
                use_elevenlabs = False
                return speak_with_google_tts(text, language)
            return False
    except Exception as e:
        print(f"\n⚠️ Error in ElevenLabs speech synthesis: {str(e)}")
        use_elevenlabs = False
        return speak_with_google_tts(text, language)

def speak_with_google_tts(text, language="en-US"):
    """Convert text to speech using Google's free Text-to-Speech API"""
    global use_voice
    
    if exit_event.is_set() or not use_voice:
        return False  # Don't speak if we're exiting or voice is disabled
    
    # Language codes mapping for Google TTS
    language_codes = {
        "en-US": "en",  # English
        "hi-IN": "hi",  # Hindi
        "te-IN": "te"   # Telugu
    }
    
    # Get the appropriate language code for Google TTS
    lang_code = language_codes.get(language, "en")
    
    try:
        print(f"\n🔊 Speaking with Google TTS in {language.split('-')[0]}...")
        
        # Create a temporary file for the speech audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3', prefix='tts_') as temp_file:
            temp_filename = temp_file.name
        
        # Generate speech audio with Google TTS
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(temp_filename)
        
        # Play the speech using pygame
        pygame.mixer.init()
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        
        # Wait for playback to finish or for exit signal
        while pygame.mixer.music.get_busy() and not exit_event.is_set():
            time.sleep(0.1)
        
        # If we need to exit, stop playback immediately
        if exit_event.is_set() and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        # Clean up the temporary file after playback
        try:
            os.remove(temp_filename)
        except:
            pass  # If file deletion fails, it will be cleaned up at exit
        
        return True
    except Exception as e:
        print(f"\n⚠️ Error in Google TTS: {str(e)}")
        use_voice = False
        return False

def speak(text, language="en-US"):
    """Speak text using the best available method"""
    if use_elevenlabs:
        # Try ElevenLabs first
        if speak_with_elevenlabs(text, language):
            return True
    
    # Fall back to Google TTS if ElevenLabs fails or is disabled
    return speak_with_google_tts(text, language)

def handle_exit_command():
    """Handle exit command with proper goodbye"""
    try:
        # Language-specific goodbyes
        goodbyes = {
            "en-US": "Goodbye! It was nice talking with you.",
            "hi-IN": "अलविदा! आपसे बात करके अच्छा लगा।",
            "te-IN": "వీడ్కోలు! మీతో మాట్లాడటం చాలా బాగుంది."
        }
        
        ai_response = goodbyes.get(selected_language, goodbyes["en-US"])
        print(f"\n🤖 AI: {ai_response}")
        if use_voice:
            speak(ai_response, selected_language)
        exit_event.set()
    except Exception as e:
        print(f"Error in exit handling: {e}")
        exit_event.set()

def real_time_listening():
    """Listen in real-time and display interim results"""
    global transcription_buffer
    
    def callback(recognizer, audio):
        """Callback for real-time speech recognition"""
        if exit_event.is_set():
            return
            
        try:
            # Get real-time transcription
            text = recognizer.recognize_google(audio, language=selected_language, show_all=False)
            if text:
                transcription_queue.put(text)
        except sr.UnknownValueError:
            pass  # Silence, no transcription
        except Exception as e:
            if not exit_event.is_set():
                print(f"\n⚠️ Error in real-time transcription: {str(e)}")
    
    # Start listening in background with real-time callback
    source = sr.Microphone()
    with source as s:
        recognizer.adjust_for_ambient_noise(s, duration=0.5)
    
    stop_listening = recognizer.listen_in_background(source, callback, phrase_time_limit=2)
    
    # Process the queue and update display in real-time
    try:
        while not exit_event.is_set():
            try:
                # Get transcription from queue with timeout
                text = transcription_queue.get(timeout=0.1)
                
                # Update the buffer
                if not transcription_buffer:
                    transcription_buffer = text
                else:
                    # Append if seems like continuation
                    transcription_buffer += " " + text
                
                # Print the ongoing transcription
                print(f"\r👂 Real-time: {transcription_buffer}", end="", flush=True)
                
                # Check for exit commands in real-time
                if check_for_exit_command(transcription_buffer, selected_language):
                    print("\n")  # Move to new line
                    return transcription_buffer
                
            except queue.Empty:
                # No new transcription, continue waiting
                pass
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_listening(wait_for_stop=False)
    
    return transcription_buffer

def process_transcription_display():
    """Process and display real-time transcription"""
    global transcription_buffer
    
    while not exit_event.is_set():
        try:
            if transcription_buffer:
                # If silence detected for more than 1.5 seconds, consider it end of utterance
                time.sleep(1.5)
                if transcription_buffer:
                    final_text = transcription_buffer
                    print("\n")  # Move to new line for final output
                    print(f"\n👤 You said: {final_text}")
                    
                    # Check for exit command
                    if check_for_exit_command(final_text, selected_language):
                        handle_exit_command()
                        break
                    
                    # Process the transcription
                    ai_response = get_ai_response(final_text, selected_language)
                    print(f"\n🤖 AI: {ai_response}")
                    
                    # Speak the response if voice is enabled
                    if use_voice:
                        speak(ai_response, selected_language)
                    
                    # Reset the buffer after processing
                    transcription_buffer = ""
        except Exception as e:
            if not exit_event.is_set():
                print(f"\n⚠️ Error in transcription processing: {str(e)}")
        
        time.sleep(0.1)

def conversation_loop():
    """Main conversation loop with real-time transcription"""
    global selected_language, transcription_buffer
    
    print("\n🎤 AI Friend is listening... (Say 'goodbye' to end the conversation)")
    
    # Start real-time listening in a thread
    listening_thread = threading.Thread(target=real_time_listening)
    listening_thread.daemon = True
    listening_thread.start()
    
    # Start processing thread
    processing_thread = threading.Thread(target=process_transcription_display)
    processing_thread.daemon = True
    processing_thread.start()
    
    # Wait for threads to complete
    try:
        while not exit_event.is_set() and (listening_thread.is_alive() or processing_thread.is_alive()):
            time.sleep(0.5)
    except KeyboardInterrupt:
        exit_event.set()

def keyboard_input_thread():
    """Monitor keyboard input for manual stop commands."""
    while not exit_event.is_set():
        try:
            cmd = input()
            if cmd.lower() in ["stop", "exit", "quit", "goodbye", "bye"]:
                print("\n⚠️ Manual stop requested via keyboard")
                handle_exit_command()
                break
        except (EOFError, KeyboardInterrupt):
            exit_event.set()
            break

def main():
    """Main function to run the voice assistant."""
    global selected_language, use_voice, use_elevenlabs
    
    # Set up signal handlers for clean termination
    signal.signal(signal.SIGINT, lambda sig, frame: end_program())
    
    print("=" * 50)
    print("🤖 Enhanced Multilingual AI Friend")
    print("=" * 50)
    print("\nThis version uses multiple ElevenLabs API keys with fallback to Google TTS!")
    
    # Check internet connectivity
    if not check_internet_connection():
        print("\n⚠️ No internet connection detected. Voice will be disabled.")
        use_voice = False
        use_elevenlabs = False
    
    # Initialize pygame mixer for audio playback
    try:
        pygame.mixer.init()
    except:
        print("\n⚠️ Could not initialize audio playback. Voice will be disabled.")
        use_voice = False
        use_elevenlabs = False
    
    # Select language
    print("\n🗣 Select language:")
    print("1. English")
    print("2. Hindi (हिन्दी)")
    print("3. Telugu (తెలుగు)")
    choice = input("Enter choice (1-3, default is 1): ").strip()
    
    lang_map = {"1": "en-US", "2": "hi-IN", "3": "te-IN"}
    selected_language = lang_map.get(choice, "en-US")
    
    language_names = {"en-US": "English", "hi-IN": "Hindi", "te-IN": "Telugu"}
    print(f"\n🌐 Selected language: {language_names.get(selected_language)}")
    
    # TTS selection
    if use_voice:
        print("\n🔊 Voice output selection:")
        print("1. ElevenLabs (High quality, with API key rotation)")
        print("2. Google TTS (Free alternative)")
        tts_choice = input("Enter choice (1-2, default is 1): ").strip()
        use_elevenlabs = tts_choice != "2"
        
        if use_elevenlabs:
            print(f"\n🔊 Using ElevenLabs with {len(ELEVEN_LABS_API_KEYS)} API keys (will fall back to Google TTS if needed)")
        else:
            print("\n🔊 Using Google TTS")
    else:
        print("\n💬 Running in text-only mode due to connectivity issues")
    
    # Language-specific welcome messages
    welcome_messages = {
        "en-US": "Hello! I'm your AI friend. How are you doing today?",
        "hi-IN": "नमस्ते! मैं आपका AI दोस्त हूँ। आज आप कैसे हैं?",
        "te-IN": "హలో! నేను మీ AI స్నేహితుడిని. మీరు ఈరోజు ఎలా ఉన్నారు?"
    }
    
    welcome_text = welcome_messages.get(selected_language, welcome_messages["en-US"])
    print(f"\n🤖 AI: {welcome_text}")
    
    if use_voice:
        speak(welcome_text, selected_language)
    
    # Reset conversation history
    conversation_history.clear()
    conversation_history.append(f"AI: {welcome_text}")
    
    # Start conversation in a separate thread
    convo_thread = threading.Thread(target=conversation_loop)
    convo_thread.daemon = True
    convo_thread.start()
    
    # Start keyboard monitoring thread
    keyboard_thread = threading.Thread(target=keyboard_input_thread)
    keyboard_thread.daemon = True
    keyboard_thread.start()
    
    # Wait for exit signal
    try:
        while not exit_event.is_set() and convo_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        exit_event.set()
    
    # Ensure proper shutdown
    print("\n🛑 Shutting down...")
    time.sleep(1)  # Give threads time to clean up
    print("\n👋 Conversation ended. Thank you for chatting!")

if __name__ == "__main__":
    main()