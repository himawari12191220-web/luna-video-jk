import os
import requests
import time
import re
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeAudioClip, TextClip, CompositeVideoClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script():
    NGROK_BASE_URL = "https://defectible-merilyn-debonairly.ngrok-free.dev/v1"
    
    payload = {
        "model": "hermes-3-llama-3.1-8b",
        "messages": [
            {
                "role": "system", 
                "content": "あなたは毒舌女子高生ルナ。冷酷な口調で怪談を書きます。余計なラベルを付けず、必ず本文、Prompt(英語)、BGM(slow, dark, tension)を出力してください。"
            },
            {
                "role": "user", 
                "content": "形式厳守：怪談本文(日本語150文字)、Prompt: (英語プロンプト)、BGM: (種類)"
            }
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{NGROK_BASE_URL}/chat/completions", json=payload, timeout=120)
        text = response.json()['choices'][0]['message']['content']
        print(f"--- AI Output ---\n{text}")

        bgm_type = "slow"
        if "tension" in text.lower(): bgm_type = "tension"
        elif "dark" in text.lower(): bgm_type = "dark"

        script = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[0].strip()
        script = re.sub(r'【.*?】|^.*?本文.*?[:：]\s*|^[0-9]\.\s*', '', script, flags=re.MULTILINE)
        
        img_prompt = "Eerie horror atmosphere"
        if "Prompt:" in text or "Prompt：" in text:
            parts = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[1]
            img_prompt = re.split(r'BGM[:：]', parts, flags=re.IGNORECASE)[0].strip()

        return script, img_prompt, bgm_type
    except:
        return "…そこにいるのは分かっているわ。でも繋がらないみたいね。", "dark room", "slow"

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed={int(time.time())}"
    try:
        res = requests.get(url, stream=True)
        if res.status_code == 200:
            with open("background.jpg", "wb") as f:
                f.write(res.content)
            return True
    except: return False

def download_voicevox(text):
    base_url = "http://localhost:50021"
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
    q = requests.post(f"{base_url}/audio_query?text={text}&speaker=2").json()
    q['speedScale'], q['intonationScale'] = 0.88, 1.9
    v = requests.post(f"{base_url}/synthesis?speaker=2", json=q)
    with open("raw_voice.wav", "wb") as f: f.write(v.content)

def make_video(script, bgm_type):
    voice = AudioFileClip("raw_voice.wav")
    bgm_path = f"bgm/{bgm_type}.mp3"
    audio = CompositeAudioClip([voice, AudioFileClip(bgm_path).volumex(0.12).set_duration(voice.duration)]) if os.path.exists(bgm_path) else voice

    bg = ImageClip("background.jpg").set_duration(voice.duration).resize(lambda t: 1 + 0.01 * t) if os.path.exists("background.jpg") else ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(voice.duration)

    # 字幕の追加：1行12文字で改行
    wrapped = "\n".join([script[i:i+12] for i in range(0, len(script), 12)])
    txt = TextClip(wrapped, fontsize=85, color='red', font='DejaVu-Sans-Bold', stroke_color='black', stroke_width=3, method='caption', size=(1000, None)).set_duration(voice.duration).set_position(('center', 950))

    CompositeVideoClip([bg, txt]).set_audio(audio).write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    s, p, b = get_horror_script()
    download_image(p)
    download_voicevox(s)
    make_video(s, b)
