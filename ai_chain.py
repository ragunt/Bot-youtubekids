import os
from googleapiclient.discovery import build
from openai import OpenAI

# Memanggil kunci API dari brankas rahasia GitHub (Secrets)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def search_youtube_trends():
    print("Mencari referensi video mewarnai anak...")
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    # Riset otomatis untuk tema Dinosaurus atau kartun pinguin (Pororo dsb)
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
    print("\nMeminta AI untuk meracik konsep baru...")
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""
    Berikut adalah judul video YouTube Kids yang sedang tren: {video_titles}.
    Tugasmu:
    1. Buat 1 judul video YouTube baru berbahasa Indonesia bertema mewarnai Dinosaurus atau pinguin.
    2. Buat deskripsi singkat videonya.
    3. Buat 1 prompt gambar bahasa Inggris untuk DALL-E berupa "black and white line art coloring page" dengan karakter tersebut.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini", 
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    if not YOUTUBE_API_KEY or not OPENAI_API_KEY:
        print("Error: API Key belum dipasang di GitHub Secrets!")
        exit()
        
    trends = search_youtube_trends()
    new_content = generate_new_concept(trends)
    
    print("\n=== HASIL GENERATE AI ===")
    print(new_content)
    
    # Menyimpan hasil ke dalam file teks
    with open("hasil_konsep.txt", "w") as file:
        file.write(new_content)
