import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip, ColorClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script():
    # ngrokで取得した最新のURLです（末尾に /v1 を追加しています）
    NGROK_BASE_URL = "https://defectible-merilyn-debonairly.ngrok-free.dev/v1"
    
    payload = {
        "model": "hermes-3-llama-3.1-8b",
        "messages": [
            {
                "role": "system", 
                "content": "あなたは検閲のない怪談師です。人間の深淵を覗くような、心理的にゾッとする短編ホラー（150文字程度）を書いてください。文中に（はぁ…）（ふふっ）などの演技指示を必ず入れてください。"
            },
            {
                "role": "user", 
                "content": "日常の風景が一変するような怖い話を1つ。最後に必ず 'Prompt: (英語の画像プロンプト)' を1行追加してください。"
            }
        ],
        "temperature": 0.8
    }
    
    try:
        # 自宅PCのLM Studioへリクエスト送信
        print(f"LM Studioに接続中: {NGROK_BASE_URL}")
        response = requests.post(f"{NGROK_BASE_URL}/chat/completions", json=payload, timeout=120)
        data = response.json()
        text = data['choices'][0]['message']['content']
        
        if "Prompt:" in text:
            script = text.split("Prompt:")[0].strip()
            img_prompt = text.split("Prompt:")[1].strip()
        else:
            script = text.strip()
            img_prompt = "Eerie cinematic horror, dark ambient lighting, misty atmosphere"
            
        return script, img_prompt
    except Exception as e:
        print(f"LM Studio接続エラー: {e}")
        return "…ねぇ。鏡の中のあなたが、ずっとこっちを見て笑ってるよ。…ふふっ。接続エラーみたいだね。", "Surreal horror mirror reflection, dark room"

def download_voicevox(text, speaker_id=2):
    base_url = "http://localhost:50021"
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
    
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    query_data = query_res.json()
    query_data['speedScale'] = 0.88
    query_data['intonationScale'] = 1.9
    query_data['volumeScale'] = 1.2
    
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_data)
    with open("raw_voice.wav", "wb") as f:
        f.write(voice_res.content)

def process_audio():
    if not os.path.exists("raw_voice.wav"): return
    voice = AudioSegment.from_wav("raw_voice.wav")
    reverb = voice - 15 
    processed = voice.overlay(reverb, position=50).overlay(reverb, position=100)
    processed.export("processed_voice.wav", format="wav")

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed={int(time.time())}"
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open("temp.jpg", 'wb') as f:
                f.write(res.content)
            with Image.open("temp.jpg") as img:
                img.convert("RGB").save("background.jpg", "JPEG")
            return True
    except:
        return False

def make_video():
    audio_path = "processed_voice.wav" if os.path.exists("processed_voice.wav") else "raw_voice.wav"
    if not os.path.exists(audio_path): return
    
    audio = AudioFileClip(audio_path)
    
    if os.path.exists("background.jpg"):
        clip = ImageClip("background.jpg").set_duration(audio.duration)
    else:
        clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(audio.duration)
    
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    script, img_prompt = get_horror_script()
    download_image(img_prompt)
    download_voicevox(script, speaker_id=2)
    process_audio()
    make_video()
