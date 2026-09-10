import os
import time
import requests
import fal_client
from googleapiclient.discovery import build
from google import genai
from google.genai.errors import ServerError

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FAL_KEY = os.getenv("FAL_KEY")  # API Key dari fal.ai yang disimpan di GitHub Secrets

def search_youtube_trends():
    print("🔍 [1/3] Mencari tren video mewarnai anak di YouTube...")
    if not YOUTUBE_API_KEY:
        print("Error: YOUTUBE_API_KEY tidak ditemukan!")
        return []
        
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        part="snippet",
        q="kids coloring page animation cute character",
        type="video",
        order="viewCount",
        maxResults=3
    )
    response = request.execute()
    video_titles = [item['snippet']['title'] for item in response['items']]
    for title in video_titles:
        print(f"   - Tren: {title}")
    return video_titles

def generate_coloring_prompt(video_titles):
    print("\n✍️ [2/3] Gemini AI merancang naskah & prompt video mewarnai...")
    if not GEMINI_API_KEY:
        print("Error: API Key Gemini kosong.")
        return "API Key Gemini kosong.", ""
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Berdasarkan tren YouTube ini: {video_titles}.
    Tugasmu:
    1. Buat judul video YouTube Kids tentang proses mewarnai 1 karakter lucu berdurasikan 1 menit (berbahasa Indonesia).
    2. Buat skrip per adegan (Scene 1 sampai 4) proses mewarnai karakter tersebut secara interaktif.
    3. Tuliskan 1 prompt visual AI video generator (dalam bahasa Inggris, gaya 3D Pixar, karakter lucu sedang diwarnai dengan sapuan warna cerah, cinematic motion) persis di baris terbawah setelah teks "PROMPT_VIDEO:".
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
                print(f"   - Server sibuk (503), mencoba ulang... ({attempt+1})")
                time.sleep(5)
            else:
                raise e
                
    text_result = response.text
    video_prompt = "3D Pixar style cute character coloring page coming to life with vibrant colors, smooth cinematic motion"
    
    if "PROMPT_VIDEO:" in text_result:
        parts = text_result.split("PROMPT_VIDEO:")
        text_result = parts[0]
        video_prompt = parts[1].strip()
        
    return text_result, video_prompt

def generate_and_download_video_via_fal(video_prompt):
    print("\n🎬 [3/3] Mengirim prompt ke Fal.ai Video API & mengunduh video...")
    if not FAL_KEY:
        print("Error: FAL_KEY tidak ditemukan di environment/secrets!")
        return False
        
    # Mengatur env key untuk fal_client
    os.environ["FAL_KEY"] = FAL_KEY
    
    try:
        # Menggunakan endpoint model video stabil di fal.ai (misalnya Kling / Text-to-Video)
        print(f"   - Prompt dikirim: {video_prompt}")
        
        handler = fal_client.submit(
            "fal-ai/kling-video/v1.6/standard/text-to-video",
            arguments={
                "prompt": video_prompt,
                "duration": "5",
                "aspect_ratio": "9:16"
            }
        )
        
        print("   - Sedang merender video di cloud Fal.ai (proses antrean)...")
        result = handler.get()
        
        if result and "video" in result and "url" in result["video"]:
            video_url = result["video"]["url"]
            print(f"   - Video berhasil dirender! Mengunduh dari: {video_url}")
            
            # Download file video ke local/GitHub
            video_response = requests.get(video_url)
            if video_response.status_code == 200:
                output_video_filename = "hasil_video_mentah.mp4"
                with open(output_video_filename, "wb") as f:
                    f.write(video_response.content)
                print(f"   - Sukses! Video tersimpan sebagai '{output_video_filename}'")
                return True
            else:
                print("   - Gagal mengunduh file video dari URL hasil.")
                return False
        else:
            print("   - Format hasil respons Fal.ai tidak sesuai.")
            return False
            
    except Exception as e:
        print(f"   - Error saat komunikasi dengan Fal.ai API: {e}")
        return False

if __name__ == "__main__":
    if not YOUTUBE_API_KEY or not GEMINI_API_KEY or not FAL_KEY:
        print("Error: Pastikan YOUTUBE_API_KEY, GEMINI_API_KEY, dan FAL_KEY sudah diatur di GitHub Secrets!")
        exit(1)
        
    print("==================================================")
    print("   ATURAN 1: OTOMATISASI PROMPT & FAL.AI VIDEO")
    print("==================================================")
    
    trends = search_youtube_trends()
    if trends:
        script_text, prompt_vid = generate_coloring_prompt(trends)
        
        print("\n📄 Naskah Cerita:")
        print(script_text)
        
        # Simpan naskah teks
        with open("naskah_cerita.txt", "w", encoding="utf-8") as f:
            f.write(script_text)
            
        # Eksekusi Aturan 1: Kirim prompt ke Fal.ai dan download videonya
        video_success = generate_and_download_video_via_fal(prompt_vid)
        
        if video_success:
            print("\n✅ Aturan 1 Selesai! Video mentah berhasil didownload.")
        else:
            print("\n⚠️ Aturan 1 menemui kendala pada proses render video.")
        print("==================================================")
    else:
        print("❌ Gagal mengambil tren YouTube.")
