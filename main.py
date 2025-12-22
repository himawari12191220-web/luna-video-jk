import os
import requests
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip

def get_luna_script(api_key):
    # Gemini 1.5 Flash を使用（多くのアカウントで最も安定して動く設定です）
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": "あなたは毒舌女子高生ルナです。世界の面白い雑学を1つ教えて。最後に画像生成用プロンプトを 'Prompt: (英語)' の形式で付けて。"}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        # AIからの返答を解析
        text = data['candidates'][0]['content']['parts'][0]['text']
        script = text.split("Prompt:")[0].strip()
        img_prompt = text.split("Prompt:")[1].strip() if "Prompt:" in text else "Anime school girl"
        return script, img_prompt
    except Exception as e:
        print(f"Error: {e}")
        return "ねぇ、ちょっと通信エラーなんだけど。次からはちゃんとしなさいよ。", "Cyberpunk girl"

def download_image(prompt):
    # 画像生成（Pollinations AI）
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=42"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video(script):
    # 音声生成
    tts = gTTS(script, lang='ja')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    # 背景画像の設定（音声の長さに合わせる）
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    
    # 動画と音声を合体
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    # GitHub Secrets から APIキーを取得
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_luna_script(api_key)
    download_image(img_prompt)
    make_video(script)
