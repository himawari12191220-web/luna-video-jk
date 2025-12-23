import os
import requests
import time
import re
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeAudioClip
from PIL import Image

def get_horror_script():
    # ngrokの固定URL
    NGROK_BASE_URL = "https://defectible-merilyn-debonairly.ngrok-free.dev/v1"
    
    payload = {
        "model": "hermes-3-llama-3.1-8b",
        "messages": [
            {"role": "system", "content": "あなたは毒舌女子高生ルナ。冷酷な口調で、怪談本文、Prompt、BGMの3点を出力してください。"},
            {"role": "user", "content": "形式厳守：怪談本文(日本語)、Prompt: (英語)、BGM: (slow, dark, tension)"}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{NGROK_BASE_URL}/chat/completions", json=payload, timeout=120)
        text = response.json()['choices'][0]['message']['content']
        
        bgm_type = "slow"
        if "tension" in text.lower(): bgm_type = "tension"
        elif "dark" in text.lower(): bgm_type = "dark"

        script = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[0].strip()
        script = re.sub(r'【.*?】|^.*?本文.*?[:：]\s*|^[0-9]\.\s*', '', script, flags=re.MULTILINE).strip()
        
        img_prompt = "Eerie horror atmosphere, cinematic lighting"
        if "Prompt:" in text or "Prompt：" in text:
            parts = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[1]
            img_prompt = re.split(r'BGM[:：]', parts, flags=re.IGNORECASE)[0].strip()

        return script, img_prompt, bgm_type
    except:
        return "…そこにいるのは分かっているわ。でも通信が繋がらないみたいね。", "dark room silhouette", "slow"

def download_image(prompt):
    # 画像生成API
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed={int(time.time())}"
    try:
        res = requests.get(url, stream=True, timeout=30)
        if res.status_code == 200:
            with open("temp_bg.jpg", "wb") as f:
                f.write(res.content)
            # 確実に読み込める形式に変換して保存
            with Image.open("temp_bg.jpg") as img:
                img.convert("RGB").save("background.jpg", "JPEG")
            return True
    except Exception as e:
        print(f"Download Error: {e}")
        return False

def download_voicevox(text):
    base_url = "http://localhost:50021"
    # 起動待ち
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
        
    q = requests.post(f"{base_url}/audio_query?text={text}&speaker=2").json()
    q['speedScale'] = 0.88
    v = requests.post(f"{base_url}/synthesis?speaker=2", json=q)
    with open("raw_voice.wav", "wb") as f: f.write(v.content)

def make_video(bgm_type):
    voice = AudioFileClip("raw_voice.wav")
    
    # BGMの設定
    bgm_path = f"bgm/{bgm_type}.mp3"
    if os.path.exists(bgm_path):
        bgm_audio = AudioFileClip(bgm_path).volumex(0.12).set_duration(voice.duration)
        final_audio = CompositeAudioClip([voice, bgm_audio])
    else:
        final_audio = voice

    # 背景の設定 (background.jpgを確実に読み込む)
    if os.path.exists("background.jpg"):
        # ゆっくりズームする演出
        bg_clip = ImageClip("background.jpg").set_duration(voice.duration)
        bg_clip = bg_clip.resize(lambda t: 1 + 0.02 * t) # 2%ズーム
    else:
        # 画像がない場合は暗い赤色の背景を生成
        bg_clip = ColorClip(size=(1080, 1920), color=(20, 0, 0)).set_duration(voice.duration)

    # 動画書き出し
    video = bg_clip.set_audio(final_audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    s, p, b = get_horror_script()
    print(f"Generating image with prompt: {p}")
    download_image(p)
    download_voicevox(s)
    make_video(b)
