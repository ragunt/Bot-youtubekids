import os
from googleapiclient.discovery import build
from google import genai

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def search_youtube_trends():
    print("Mencari referensi video mewarnai anak...")
    if not YOUTUBE_API_KEY:
        print("Error: YOUTUBE_API_KEY tidak ditemukan!")
        return []
        
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    request = youtube.search().list(
        part="snippet",
        q="dinosaur coloring page kids OR pororo coloring kids",
        type="video",
        order="viewCount",
        maxResults=3
    )
    response = request.execute()
    
    video_titles = [item['snippet']['title'] for item in response['items']]
    for title in video_titles:
        print(f"- Referensi ditemukan: {title}")
        
    return video_titles

def generate_new_concept(video_titles):
    print("\nMeminta Gemini AI untuk meracik konsep baru...")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY tidak ditemukan!")
        return "API Key Gemini kosong."
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Berikut adalah judul video YouTube Kids yang sedang tren: {video_titles}.
    Tugasmu:
    1. Buat 1 judul video YouTube baru berbahasa Indonesia bertema mewarnai Dinosaurus atau pinguin.
    2. Buat deskripsi singkat videonya.
    3. Buat 1 prompt gambar bahasa Inggris untuk DALL-E berupa "black and white line art coloring page" dengan karakter tersebut.
    """
    
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )
    
    return response.text

if __name__ == "__main__":
    if not YOUTUBE_API_KEY or not GEMINI_API_KEY:
        print("Error: Salah satu atau kedua API Key belum dipasang di GitHub Secrets!")
        exit(1)
        
    trends = search_youtube_trends()
    if trends:
        new_content = generate_new_concept(trends)
        
        print("\n=== HASIL GENERATE AI ===")
        print(new_content)
        
        with open("hasil_konsep.txt", "w") as file:
            file.write(new_content)
    else:
        print("Gagal mengambil tren YouTube.")
