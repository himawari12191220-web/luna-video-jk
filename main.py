import os
import requests
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeVideoClip

def get_luna_script(api_key):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "あなたは毒舌女子高生ルナです。世界の面白い雑学を1つ教えて。最後に画像生成用プロンプトを 'Prompt: (英語)' の形式で付けて。"}]}],
        "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}]
    }
    response = requests.post(url, json=payload)
    data = response.json()
    
    if 'candidates' not in data:
        return "ねぇ、通信エラーなんだけど。やる気出しなさいよ。", "Cyberpunk girl"
    
    text = data['candidates'][0]['content']['parts'][0]['text']
    script = text.split("Prompt:")[0].strip()
    img_prompt = text.split("Prompt:")[1].strip() if "Prompt:" in text else "Anime school girl"
    return script, img_prompt

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=42"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video(script):
    # 音声生成
    tts = gTTS(script, lang='ja')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    # 背景画像（音声の長さに合わせる）
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    
    # 【修正ポイント】ImageMagickを使わない動画合成
    # 字幕なしで、背景と音声だけで動画を作成（エラーを100%回避）
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_luna_script(api_key)
    download_image(img_prompt)
    make_video(script)
