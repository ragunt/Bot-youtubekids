import os
import time
import requests
# --- PATCH PIL UNTUK MOVIEPY ---
from PIL import Image
Image.ANTIALIAS = Image.LANCZOS
# --- AKHIR PATCH ---
import cv2
import numpy as np
from googleapiclient.discovery import build
from google import genai
from google.genai.errors import ServerError
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips

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
    1. Buat 1 judul video YouTube baru berbahasa Indonesia bertema mewarnai Dinosaurus atau pinguin (singkat & menarik).
    2. Buat deskripsi singkat videonya.
    3. Buat 1 prompt gambar bahasa Inggris khusus untuk line art: "black and white line art coloring page, thick black outlines, cute character, white background, no shading". Berikan promptnya di baris paling bawah setelah teks "PROMPT_IMG:".
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

def generate_and_save_images(prompt_text):
    print("\nSedang mendesain gambar line art & versi warnanya...")
    
    # 1. Unduh Line Art (Hitam Putih)
    encoded_prompt_bw = requests.utils.quote(prompt_text)
    url_bw = f"https://image.pollinations.ai/prompt/{encoded_prompt_bw}?width=720&height=1280&nologo=true"
    
    # 2. Unduh Versi Berwarna (Full Color Cartoon)
    prompt_color = prompt_text.replace("black and white line art", "vibrant colorful digital illustration, cute cartoon style, kids animation background")
    encoded_prompt_color = requests.utils.quote(prompt_color)
    url_color = f"https://image.pollinations.ai/prompt/{encoded_prompt_color}?width=720&height=1280&nologo=true"
    
    try:
        r_bw = requests.get(url_bw)
        r_color = requests.get(url_color)
        
        if r_bw.status_code == 200 and r_color.status_code == 200:
            with open("line_art.png", "wb") as f:
                f.write(r_bw.content)
            with open("full_color.png", "wb") as f:
                f.write(r_color.content)
            print("Gambar Line Art dan Full Color berhasil dibuat!")
            return True
        else:
            print("Gagal mengunduh aset gambar.")
            return False
    except Exception as e:
        print(f"Error saat mengunduh gambar: {e}")
        return False

def create_animated_coloring_video():
    print("\nMerakit video animasi proses mewarnai hidup...")
    if not os.path.exists("line_art.png") or not os.path.exists("full_color.png"):
        print("Aset gambar tidak lengkap.")
        return
        
    try:
        # Durasi total video 10 detik
        # Bagian 1: Menampilkan Line Art (Hitam Putih) selama 3 detik
        clip_bw = ImageClip("line_art.png").set_duration(3)
        
        # Bagian 2: Efek Transisi Masuk ke Full Color secara perlahan (Fade-in mewarnai) selama 4 detik
        clip_color = ImageClip("full_color.png").set_duration(4).crossfadein(2)
        
        # Bagian 3: Hasil Akhir Berwarna selama 3 detik
        clip_final = ImageClip("full_color.png").set_duration(3)
        
        # Gabungkan klip menjadi satu video utuh
        final_video = concatenate_videoclips([clip_bw, clip_color, clip_final], method="compose")
        
        output_video = "hasil_video_youtube.mp4"
        final_video.write_videofile(output_video, fps=24, codec="libx264", audio=False)
        print(f"Video animasi hidup berhasil dirender sebagai {output_video}!")
    except Exception as e:
        print(f"Error saat merakit animasi video: {e}")

if __name__ == "__main__":
    if not YOUTUBE_API_KEY or not GEMINI_API_KEY:
        print("Error: API Key belum lengkap di GitHub Secrets!")
        exit(1)
        
    trends = search_youtube_trends()
    if trends:
        new_content, img_prompt = generate_new_concept(trends)
        
        print("\n=== HASIL GENERATE KONTEN ==="")
        print(new_content)
        
        image_success = generate_and_save_images(img_prompt)
        
        if image_success:
            create_animated_coloring_video()
        
        with open("hasil_konsep.txt", "w") as file:
            file.write(new_content + f"\n\nPROMPT_IMG: {img_prompt}")
    else:
        print("Gagal mengambil tren YouTube.")
