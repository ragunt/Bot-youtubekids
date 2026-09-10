import os
import time
import requests
from googleapiclient.discovery import build
from google import genai
from google.genai.errors import ServerError
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip

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
    print("\nMeminta Gemini AI untuk meracik konsep & prompt gambar...")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY tidak ditemukan!")
        return "API Key Gemini kosong.", ""
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Berikut adalah judul video YouTube Kids yang sedang tren: {video_titles}.
    Tugasmu:
    1. Buat 1 judul video YouTube baru berbahasa Indonesia bertema mewarnai Dinosaurus atau pinguin.
    2. Buat deskripsi singkat videonya.
    3. Buat 1 prompt gambar bahasa Inggris yang sangat detail khusus untuk generator gambar berupa "black and white line art coloring page, thick black outlines, cute character, white background, no shading". Berikan prompt gambarnya saja di bagian paling bawah setelah teks "PROMPT_IMG:".
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt,
            )
            break
        except ServerError as e:
            if attempt < max_retries - 1:
                print(f"Server Gemini sibuk (503), mencoba ulang dalam 5 detik... (Percobaan ke-{attempt+1})")
                time.sleep(5)
            else:
                raise e
    
    text_result = response.text
    
    img_prompt = "cute dinosaur coloring page for kids, black and white line art, thick outlines"
    if "PROMPT_IMG:" in text_result:
        parts = text_result.split("PROMPT_IMG:")
        text_result = parts[0]
        img_prompt = parts[1].strip()
        
    return text_result, img_prompt

def generate_and_save_image(prompt_text):
    print("\nSedang mendesain gambar mewarnai otomatis...")
    encoded_prompt = requests.utils.quote(prompt_text)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open("hasil_coloring.png", "wb") as handler:
                handler.write(response.content)
            print("Gambar berhasil dibuat dan disimpan sebagai hasil_coloring.png!")
            return True
        else:
            print("Gagal mengunduh gambar.")
            return False
    except Exception as e:
        print(f"Error saat membuat gambar: {e}")
        return False

def create_video_from_image():
    print("\nMerakit video otomatis dari gambar...")
    if not os.path.exists("hasil_coloring.png"):
        print("File gambar tidak ditemukan, batal membuat video.")
        return
        
    try:
        # Membuat video berdurasi 5 detik dari gambar hasil coloring
        clip = ImageClip("hasil_coloring.png").set_duration(5)
        # Menetapkan ukuran resolusi video vertikal (cocok untuk YouTube Shorts / TikTok)
        clip = clip.resize(width=720, height=1280)
        
        # Render video ke format MP4
        output_video = "hasil_video_youtube.mp4"
        clip.write_videofile(output_video, fps=24, codec="libx264", audio=False)
        print(f"Video berhasil dibuat dan disimpan sebagai {output_video}!")
    except Exception as e:
        print(f"Error saat merakit video: {e}")

if __name__ == "__main__":
    if not YOUTUBE_API_KEY or not GEMINI_API_KEY:
        print("Error: API Key belum lengkap di GitHub Secrets!")
        exit(1)
        
    trends = search_youtube_trends()
    if trends:
        new_content, img_prompt = generate_new_concept(trends)
        
        print("\n=== HASIL GENERATE KONTEN ===")
        print(new_content)
        print(f"\nPrompt Gambar Terpilih: {img_prompt}")
        
        # 1. Buat Gambar
        image_success = generate_and_save_image(img_prompt)
        
        # 2. Rangkai Menjadi Video Jika Gambar Berhasil Dibuat
        if image_success:
            create_video_from_image()
        
        with open("hasil_konsep.txt", "w") as file:
            file.write(new_content + f"\n\nPROMPT_IMG: {img_prompt}")
    else:
        print("Gagal mengambil tren YouTube.")
