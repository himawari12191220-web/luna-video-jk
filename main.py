import os
import requests
import time
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip

def get_luna_script(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": """
        あなたは都市伝説テラーの『カイ』です。
        視聴者の背筋が凍るような、怖くて引き込まれる話を1つ教えてください。
        
        【話し方の指示】
        ・人間が語りかけるように、自然な「。、」を入れてください。
        ・冒頭は「...ねぇ、これ信じるかどうかはお任せします。」
        ・最後は「...今の足音、君の家じゃないよね？」
        ・物語の途中で「...」を使い、タメ（間）を作ってください。
        
        【出力形式】
        物語の内容
        Prompt: (英語の画像生成プロンプト)
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
        img_prompt = "Dark eerie cinematic horror " + (text.split("Prompt:")[1].strip() if "Prompt:" in text else "abandoned asylum")
        return script, img_prompt
    except:
        return "...ねぇ、後ろに誰かいない？...なんてね、通信エラーだよ。", "Dark spooky ghost"

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=99"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video(script):
    # 【人間らしくする工夫】。や、の後に読点を増やして「間」を作る
    fluent_script = script.replace("。", "。。。").replace("、", "、 ")
    
    tts = gTTS(fluent_script, lang='ja')
    tts.save("voice.mp3")
    time.sleep(2)
    
    audio = AudioFileClip("voice.mp3")
    
    # 読み上げ速度が速すぎると機械的なので、音声を0.9倍速にして落ち着きを出す
    # ※MoviePyのバージョンにより動作が異なるため、一旦標準速度で合体
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_luna_script(api_key)
    download_image(img_prompt)
    make_video(script)
