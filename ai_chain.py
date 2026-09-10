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
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def search_youtube_trends():
    print("Mencari referensi tren kartun anak...")
    if not YOUTUBE_API_KEY:
        print("Error: YOUTUBE_API_KEY tidak ditemukan!")
        return []
        
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet",
        q="kids cartoon animation dinosaur OR cute toddler story video",
        type="video",
        order="viewCount",
        maxResults=3
    )
    response = request.execute()
    video_titles = [item['snippet']['title'] for item in response['items']]
    for title in video_titles:
        print(f"- Referensi ditemukan: {title}")
    return video_titles

def generate_cartoon_script(video_titles):
    print("\nMeminta Gemini AI untuk merancang episode kartun anak harian...")
    if not GEMINI_API_KEY:
        print("Error: API Key Gemini kosong.")
        return "API Key Gemini kosong.", ""
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Berdasarkan tren YouTube Kids ini: {video_titles}.
    Tugasmu:
    1. Buat 1 judul episode kartun anak berbahasa Indonesia yang menarik dan ramah anak.
    2. Buat alur cerita singkat (skrip episode harian).
    3. Buat 1 prompt visual gambar animasi 3D gaya Pixar yang sangat hidup, ceria, dan penuh warna untuk adegan utama (dalam bahasa Inggris). Berikan promptnya di baris paling bawah setelah teks "PROMPT_IMG:".
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
    img_prompt = "3D Pixar style animated cute baby dinosaur having a happy adventure in a colorful magical forest, vibrant lighting, cinematic"
    if "PROMPT_IMG:" in text_result:
        parts = text_result.split("PROMPT_IMG:")
        text_result = parts[0]
        img_prompt = parts[1].strip()
        
    return text_result, img_prompt

def generate_and_save_visuals(prompt_text):
    print("\nSedang mendesain visual utama episode kartun...")
    
    encoded_prompt = requests.utils.quote(prompt_text + ", high quality, 4k resolution")
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&nologo=true&seed=100"
    
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open("episode_scene.png", "wb") as f:
                f.write(response.content)
            print("Visual episode berhasil dibuat!")
            return True
        else:
            print("Gagal mengunduh visual.")
            return False
    except Exception as e:
        print(f"Error saat mengunduh visual: {e}")
        return False

def create_episode_video():
    print("\nMerakit video episode kartun sinematik dengan efek gerak dinamis...")
    if not os.path.exists("episode_scene.png"):
        print("File visual tidak ditemukan.")
        return
        
    try:
        def cinematic_zoom(get_frame, t):
            img = get_frame(t)
            h, w, _ = img.shape
            zoom_factor = 1.0 + (0.10 * (t / 15.0))
            new_h, new_w = int(h * zoom_factor), int(w * zoom_factor)
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            start_y = (new_h - h) // 2
            start_x = (new_w - w) // 2
            return resized[start_y:start_y+h, start_x:start_x+w]

        clip1 = ImageClip("episode_scene.png").set_duration(15).fl(cinematic_zoom)
        clip2 = ImageClip("episode_scene.png").set_duration(15).fl(cinematic_zoom).crossfadein(2)
        
        final_video = concatenate_videoclips([clip1, clip2], method="compose")
        
        if os.path.exists("musik_anak.mp3"):
            print("Menyematkan musik latar anak-anak...")
            audio = AudioFileClip("musik_anak.mp3").subclip(0, 30)
            final_video = final_video.set_audio(audio)
            
        output_video = "hasil_video_youtube.mp4"
        final_video.write_videofile(output_video, fps=24, codec="libx264", audio=os.path.exists("musik_anak.mp3"))
        print(f"Episode kartun harian berhasil dirender sebagai {output_video}!")
    except Exception as e:
        print(f"Error saat merakit video episode: {e}")

if __name__ == "__main__":
    if not YOUTUBE_API_KEY or not GEMINI_API_KEY:
        print("Error: API Key belum lengkap di GitHub Secrets!")
        exit(1)
        
    trends = search_youtube_trends()
    if trends:
        cartoon_script, img_prompt = generate_cartoon_script(trends)
        
        print("\n=== SKRIP EPISODE & PROMPT HARIAN ===")
        print(cartoon_script)
        
        visual_success = generate_and_save_visuals(img_prompt)
        
        if visual_success:
            create_episode_video()
            
        with open("hasil_konsep.txt", "w") as file:
            file.write(cartoon_script + f"\n\nPROMPT_IMG: {img_prompt}")
    else:
        print("Gagal mengambil tren YouTube.")
