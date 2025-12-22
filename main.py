import os
import requests
import time
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip

def get_luna_script(api_key):
    # Gemini 3 Flash Preview 用のURL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": """
        あなたは都市伝説テラーの『カイ』です。
        視聴者が夜寝られなくなるような、短くてゾッとする怖い話や都市伝説を1つくれて。
        【ルール】
        ・冒頭は必ず「...ねぇ、これ信じるかどうかはお任せします。」から始める。
        ・最後は「...今の足音、君の家じゃないよね？」で締める。
        ・全体で30秒以内の音声になる長さ。
        ・最後に、その話に合う不気味な画像生成用英語プロンプトを「Prompt: (英語)」の形式で出力して。
        """}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        text = data['candidates'][0]['content']['parts'][0]['text']
        script = text.split("Prompt:")[0].strip()
        # 画像をより不気味にするためにDark, Eerieというキーワードを固定で追加
        img_prompt = "Dark eerie " + (text.split("Prompt:")[1].strip() if "Prompt:" in text else "horror abandoned house")
        return script, img_prompt
    except:
        return "...ねぇ、後ろに誰かいない？...なんてね、通信エラーだよ。", "Dark spooky ghost"

def download_image(prompt):
    # ホラー風の画像を生成
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=66"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video(script):
    tts = gTTS(script, lang='ja')
    tts.save("voice.mp3")
    time.sleep(2)
    
    audio = AudioFileClip("voice.mp3")
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_luna_script(api_key)
    download_image(img_prompt)
    make_video(script)
