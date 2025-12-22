import os
import requests
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings

# Linux環境用の設定
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

def get_luna_script(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # 安全フィルターを無効化してエラーを回避する設定
    payload = {
        "contents": [{"parts": [{"text": "あなたは少し毒舌な女子高生ルナです。世界の面白い雑学を1つ教えて。最後に画像生成用プロンプトを 'Prompt: (英語)' の形式で付けて。"}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    # エラーチェックを追加
    if 'candidates' not in data:
        print("Google AIからの応答エラー:", data)
        return "ねぇ、ちょっと通信エラーなんだけど。やる気出しなさいよ。", "Cyberpunk girl"

    text = data['candidates'][0]['content']['parts'][0]['text']
    script = text.split("Prompt:")[0].strip()
    img_prompt = text.split("Prompt:")[1].strip() if "Prompt:" in text else "Anime school girl"
    return script, img_prompt

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=42"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video(script):
    tts = gTTS(script, lang='ja')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    # フォントエラー対策：デフォルトフォントを使用
    txt = TextClip(script, fontsize=50, color='white', method='caption', size=(900, None)).set_duration(audio.duration)
    
    video = CompositeVideoClip([clip, txt.set_position('center')])
    video.set_audio(audio).write_videofile("output.mp4", fps=24, codec="libx264")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_luna_script(api_key)
    download_image(img_prompt)
    make_video(script)
