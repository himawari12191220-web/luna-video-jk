import os
import requests
import time
import re
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeAudioClip, TextClip, CompositeVideoClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script():
    # 画像1の固定ドメインを設定済み
    NGROK_BASE_URL = "https://defectible-merilyn-debonairly.ngrok-free.dev/v1"
    
    payload = {
        "model": "hermes-3-llama-3.1-8b", # 画像3, 4のモデル名
        "messages": [
            {
                "role": "system", 
                "content": "あなたは毒舌女子高生ルナ。冷酷な口調で、余計な解説を省き、怪談本文、Prompt、BGMの3点を出力してください。"
            },
            {
                "role": "user", 
                "content": "【形式厳守】怪談本文(日本語)、Prompt: (英語)、BGM: (slow, dark, tensionのいずれか)"
            }
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{NGROK_BASE_URL}/chat/completions", json=payload, timeout=120)
        text = response.json()['choices'][0]['message']['content']
        print(f"--- AI Output ---\n{text}")

        # BGM判定
        bgm_type = "slow"
        lower_text = text.lower()
        if "tension" in lower_text: bgm_type = "tension"
        elif "dark" in lower_text: bgm_type = "dark"

        # 台本クリーニング：ラベルや余計な前置きを排除
        script = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[0].strip()
        script = re.sub(r'【.*?】|^.*?本文.*?[:：]\s*|^[0-9]\.\s*|^.*?怪談.*?[:：]\s*', '', script, flags=re.MULTILINE)
        script = script.strip()

        # プロンプト抽出
        img_prompt = "Eerie horror atmosphere, cinematic lighting"
        if "Prompt:" in text or "Prompt：" in text:
            parts = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[1]
            img_prompt = re.split(r'BGM[:：]', parts, flags=re.IGNORECASE)[0].strip()

        return script, img_prompt, bgm_type
    except:
        return "…そこにいるのは分かっているわ。でも通信が繋がらないみたいね。", "dark room silhouette", "slow"

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed={int(time.time())}"
    try:
        res = requests.get(url, stream=True, timeout=30)
        if res.status_code == 200:
            with open("background.jpg", "wb") as f: f.write(res.content)
            # 画像読み込みエラー対策としてRGB形式で保存し直す
            with Image.open("background.jpg") as img:
                img.convert("RGB").save("background.jpg", "JPEG")
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

    # 画像読み込みエラー対策
    try:
        bg = ImageClip("background.jpg").set_duration(voice.duration).resize(lambda t: 1 + 0.01 * t)
    except:
        bg = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(voice.duration)

    # 赤い大きな字幕の作成
    wrapped = "\n".join([script[i:i+12] for i in range(0, len(script), 12)])
    txt = TextClip(
        wrapped, 
        fontsize=85, 
        color='red', 
        font='DejaVu-Sans-Bold', 
        stroke_color='black', 
        stroke_width=3, 
        method='caption', 
        size=(1000, None)
    ).set_duration(voice.duration).set_position(('center', 950))

    CompositeVideoClip([bg, txt]).set_audio(audio).write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    s, p, b = get_horror_script()
    download_image(p)
    download_voicevox(s)
    make_video(s, b)
