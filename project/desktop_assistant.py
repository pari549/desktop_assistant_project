import os
import re
import sys
import webbrowser
import datetime
import urllib.parse
import speech_recognition as sr
import pyttsx3
from difflib import get_close_matches

# Optional: load .env for local dev
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# ----------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------
BROWSER_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
VIDEO_PATH = r"C:\Users\KIIT0001\Downloads\YOUTUBE\part-3.mp4"

SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "netflix": "https://www.netflix.com",
    "whatsapp": "https://web.whatsapp.com",
    "spotify": "https://open.spotify.com",
    "linkedin": "https://www.linkedin.com",
    "instagram": "https://www.instagram.com",
    "chatgpt": "https://chat.openai.com",
}

APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
}

# ----------------------------------------------------
# OPENAI CLIENT (via environment variable)
# ----------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_openai_client():
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=OPENAI_API_KEY)
    except:
        return None

# ----------------------------------------------------
# TEXT-TO-SPEECH SETUP
# ----------------------------------------------------
tts = pyttsx3.init()
tts.setProperty("rate", 170)
tts.setProperty("volume", 1.0)

def speak(text):
    print(f"\nAssistant: {text}\n")
    try:
        tts.say(text)
        tts.runAndWait()
    except:
        pass

# ----------------------------------------------------
# SPEECH-TO-TEXT SETUP
# ----------------------------------------------------
recognizer = sr.Recognizer()

def listen(timeout=8, phrase_time_limit=10):
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            print("Recognizing...")
            text = recognizer.recognize_google(audio, language="en-in")
            print(f"You said: {text}")
            return text.lower()
    except sr.WaitTimeoutError:
        print("No voice detected.")
        return None
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return None
    except sr.RequestError as e:
        print("Speech service error:", e)
        return None

# ----------------------------------------------------
# INTENT DETECTION
# ----------------------------------------------------
def fuzzy_find_name(word, candidates, cutoff=0.6):
    if not word:
        return None
    if word in candidates:
        return word
    tokens = word.split()
    for t in tokens:
        if t in candidates:
            return t
    matches = get_close_matches(word, candidates.keys(), n=1, cutoff=cutoff)
    if matches:
        return matches[0]
    for k in candidates:
        if k in word or word in k:
            return k
    return None

def detect_intent_and_payload(text):
    if not text:
        return None, None

    if any(w in text for w in ["exit", "quit", "stop", "bye", "goodbye"]):
        return "exit", None
    if "time" in text:
        return "time", None
    if "play video" in text or "open video" in text:
        return "play_video", VIDEO_PATH
    if text.startswith("search ") or "search for" in text:
        q = re.sub(r"^(search|find)\s*(for)?\s*", "", text, flags=re.I).strip()
        return "search", q

    for site_name in SITES:
        if site_name in text:
            return "open_site", SITES[site_name]

    open_match = re.search(r"\b(open|go to|launch|website|site)\b\s*(.*)", text)
    if open_match:
        target = open_match.group(2).strip()
        best = fuzzy_find_name(target, SITES)
        if best:
            return "open_site", SITES[best]

    for app_name in APPS:
        if app_name in text:
            return "open_app", APPS[app_name]

    open_app_match = re.search(r"\b(open|launch|start|run)\b\s*(.*)", text)
    if open_app_match:
        target = open_app_match.group(2).strip()
        best = fuzzy_find_name(target, APPS)
        if best:
            return "open_app", APPS[best]

    return "chat", text

# ----------------------------------------------------
# ACTION HANDLERS
# ----------------------------------------------------
def handle_open_site(url):
    try:
        if os.path.exists(BROWSER_PATH):
            webbrowser.register('mybrowser', None, webbrowser.BackgroundBrowser(BROWSER_PATH))
            webbrowser.get('mybrowser').open(url)
        else:
            webbrowser.open(url)
        speak("Opened the website for you.")
    except Exception as e:
        print("Website error:", e)
        speak("Sorry, I could not open the website.")

def handle_open_app(cmd):
    try:
        os.startfile(cmd)
        speak("Opening the application.")
    except Exception as e:
        print("App error:", e)
        speak("Sorry, I could not open that application.")

def handle_search(query):
    if not query:
        speak("What should I search for?")
        return
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    handle_open_site(url)
    speak(f"Searching for {query}.")

def handle_time():
    now = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The time is {now}.")

def handle_play_video(path):
    if os.path.exists(path):
        os.startfile(path)
        speak("Playing your video.")
    else:
        speak("Video file not found.")

def handle_chat(text):
    client = get_openai_client()
    if client is None:
        speak("Chat is unavailable because the API key is not configured.")
        return
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a smart, friendly, polite AI desktop assistant."},
                {"role": "user", "content": text},
            ],
        )
        answer = response.choices[0].message.content.strip()
        speak(answer)
    except Exception as e:
        print("GPT error:", e)
        speak("Sorry, I could not connect to the AI service right now.")

# ----------------------------------------------------
# MAIN LOOP
# ----------------------------------------------------
def main_loop():
    speak("Hello, I am your AI desktop assistant. How can I help you today?")
    try:
        while True:
            text = listen(timeout=8, phrase_time_limit=10)
            if text is None:
                continue
            intent, payload = detect_intent_and_payload(text)
            print("Detected intent:", intent, "| Payload:", payload)

            if intent == "exit":
                speak("Okay, goodbye. Have a great day.")
                break
            elif intent == "time":
                handle_time()
            elif intent == "open_site":
                handle_open_site(payload)
            elif intent == "open_app":
                handle_open_app(payload)
            elif intent == "search":
                handle_search(payload)
            elif intent == "play_video":
                handle_play_video(payload)
            elif intent == "chat":
                handle_chat(payload)
            else:
                speak("Sorry, I did not understand that.")
    except KeyboardInterrupt:
        speak("Stopping. Bye.")
        sys.exit(0)

# ----------------------------------------------------
# RUN
# ----------------------------------------------------
if __name__ == "__main__":
    main_loop()
