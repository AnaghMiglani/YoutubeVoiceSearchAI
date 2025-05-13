import speech_recognition as sr
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import isodate
import google.generativeai as genai
from datetime import datetime, timedelta, timezone

# genai.configure(api_key="AIzaSyBZeTyKGXwuoPeVcVyL47jIGfqMmlPNbzc")
# for m in genai.list_models():
#        if 'generateContent' in m.supported_generation_methods:
#            print(m.name)


# get voice input or fallback to text
def get_voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak your YouTube search query:")
        audio = r.listen(source)
        try:
            query = r.recognize_google(audio)
            print("You said:", query)
            return query
        except sr.UnknownValueError:
            print("Could not understand audio.")
        except sr.RequestError as e:
            print(f"Speech Recognition error: {e}")
    return None

query = get_voice_input() or input("Enter your search query: ")

# searching YouTube using API (Youtube Data API v3)
def search_youtube(query):
    api_key = "AIzaSyDCGHvZ7ka9GapR8dvfbSfcs8hpBSxTzLc"  #hardcoded for now (for submission)
    youtube = build("youtube", "v3", developerKey=api_key)

    try:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=20,
            publishedAfter=(datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        )
        response = request.execute()
    except Exception as e:
        print("YouTube API Error:", e)
        return []

    video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
    if not video_ids:
        return []

    try:
        details = youtube.videos().list(
            part="snippet,contentDetails",
            id=",".join(video_ids)
        ).execute()
    except Exception as e:
        print("Error fetching video details:", e)
        return []

    results = []
    for item in details.get("items", []):
        duration = item["contentDetails"]["duration"]
        duration_seconds = isodate.parse_duration(duration).total_seconds()
        if 240 <= duration_seconds <= 1200: # 4 to 20 minutes
            results.append({
                "title": item["snippet"]["title"],
                "url": f"https://www.youtube.com/watch?v={item['id']}"
            })
    return results

# Ranking with Gemini AI
def rank_with_gemini(videos, query):
    genai.configure(api_key="AIzaSyBZeTyKGXwuoPeVcVyL47jIGfqMmlPNbzc") #hardcoded for now (for submission)
    model = genai.GenerativeModel("models/gemini-2.0-flash")

    titles_text = "\n".join([f"{i+1}. {v['title']}" for i, v in enumerate(videos)])
    prompt = f"""
You are a YouTube video assistant. Below is a list of video titles:
{titles_text}
Which of these seems most relevant and high-quality for the query: '{query}'? Reply with the best one and why.
"""
    response = model.generate_content(prompt)
    return response.text

# Display results
print("\nSearching for videos...")
videos = search_youtube(query)
if not videos:
    print("No matching videos found.")
else:
    print("\nTop videos found:")
    for v in videos:
        print("-", v["title"], "→", v["url"])

    gemini_result = rank_with_gemini(videos, query)
    print("\nBest Picks:\n", gemini_result)
