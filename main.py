import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip

def get_horror_script(api_key):
    # Gemini 3 Flash Preview のエンドポイント
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": """
                あなたは都市伝説テラーの『カイ』です。
                聴いた人が思わず後ろを振り返ってしまうような、短くも強烈な恐怖体験を1つ語ってください。
                
                【語り口の指示】
                ・冒頭は「...ねぇ、これ、あなたの身に起きたことじゃないよね？」
                ・最後は「...今の物音、君の家じゃないよね？」
                ・人間らしい『間』を意識して、適宜「...」を入れてください。
                
                【出力形式】
                物語の内容
                Prompt: (英語の不気味な画像生成プロンプト)
                """
            }]
        }],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    # 応答チェック
    if 'candidates' not in data:
        return "...ねぇ、後ろに誰かいない？...なんてね、通信エラーだよ。", "Spooky dark room"

    text = data['candidates'][0]['content']['parts'][0]['text']
    script = text.split("Prompt:")[0].strip()
    img_prompt = "Cinematic horror style " + (text.split("Prompt:")[1].strip() if "Prompt:" in text else "haunted dark forest")
    return script, img_prompt

def download_voicevox(text, speaker_id=2):
    base_url = "http://localhost:50021"
    
    # エンジンの起動を待機
    print("VOICEVOXエンジン起動待ち...")
    for _ in range(30):
        try:
            if requests.get(f"{base_url}/version").status_code == 200:
                break
        except:
            time.sleep(1)
    
    # 1. 音声合成用のクエリを作成
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    # 2. 音声合成を実行
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_res.json())
    
    with open("voice.wav", "wb") as f:
        f.write(voice_res.content)
    return True

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=13"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video():
    audio = AudioFileClip("voice.wav")
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_horror_script(api_key)
    download_image(img_prompt)
    if download_voicevox(script, speaker_id=2):
        make_video()
