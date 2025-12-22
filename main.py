import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip, ColorClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script(api_key):
    # Gemini 3 Flash / 1.5 Flash の最新エンドポイント
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "あなたは伝説の怪談師です。視聴者が夜、一人でいるのを後悔するような短い怖い話を1つ語ってください。文中に（はぁ…）（ふふっ）を必ず入れ、恐怖を演出してください。最後に 'Prompt: (英語の不気味な画像プロンプト)' を付けて。"
            }]
        }],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        # AIが回答を拒否した場合はログを出して予備セリフへ
        if 'candidates' not in data or not data['candidates'][0].get('content'):
            print("API Response Error:", data)
            return "…ねぇ、後ろに誰かいない？…なんてね。通信エラーだよ。次はちゃんとしてね。", "Eerie silhouette in dark room"

        text = data['candidates'][0]['content']['parts'][0]['text']
        script = text.split("Prompt:")[0].strip()
        img_prompt = (text.split("Prompt:")[1].strip() if "Prompt:" in text else "dark haunted hallway")
        return script, img_prompt
    except:
        return "…システムに何かが入り込んだみたい。通信エラーだよ。", "Glitched digital ghost"

def download_voicevox(text, speaker_id=2):
    base_url = "http://localhost:50021"
    # VOICEVOXエンジンの起動待ち
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
    
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    query_data = query_res.json()
    query_data['speedScale'] = 0.85
    query_data['intonationScale'] = 1.7
    
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_data)
    with open("raw_voice.wav", "wb") as f:
        f.write(voice_res.content)

def process_audio():
    if not os.path.exists("raw_voice.wav"): return
    voice = AudioSegment.from_wav("raw_voice.wav")
    # リバーブ加工（残響）
    reverb = voice - 15 
    processed = voice.overlay(reverb, position=60).overlay(reverb, position=120)
    processed.export("processed_voice.wav", format="wav")

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed={int(time.time())}"
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open("temp.jpg", 'wb') as f: f.write(res.content)
            with Image.open("temp.jpg") as img: img.convert("RGB").save("background.jpg", "JPEG")
            return True
    except: return False

def make_video():
    audio_path = "processed_voice.wav" if os.path.exists("processed_voice.wav") else "raw_voice.wav"
    if not os.path.exists(audio_path): return
    audio = AudioFileClip(audio_path)
    if os.path.exists("background.jpg"):
        clip = ImageClip("background.jpg").set_duration(audio.duration)
    else:
        # 画像がない場合は黒画面で対応（エラー回避）
        clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(audio.duration)
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_horror_script(api_key)
    download_image(img_prompt)
    download_voicevox(script, speaker_id=2)
    process_audio()
    make_video()
