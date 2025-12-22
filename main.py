import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip

def get_horror_script(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": """
        あなたは都市伝説テラーの『カイ』です。
        短くて、聴いた後に「自分の部屋が怖くなる」ような話を1つ作ってください。
        
        【話し方の指示】
        ・人間が語りかけるように、自然な「。、」を入れてください。
        ・冒頭は「...ねぇ、これ信じるかどうかはお任せします。」
        ・最後は「...今の足音、君の家じゃないよね？」
        ・物語の途中で「...」を使い、タメ（間）を作ってください。
        
        【出力形式】
        物語の内容
        Prompt: (英語の画像生成プロンプト)
        """}]}],
        "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}]
    }
    response = requests.post(url, json=payload)
    text = response.json()['candidates'][0]['content']['parts'][0]['text']
    script = text.split("Prompt:")[0].strip()
    img_prompt = "Dark eerie cinematic horror " + (text.split("Prompt:")[1].strip() if "Prompt:" in text else "abandoned asylum")
    return script, img_prompt

def download_voicevox(text, speaker_id=3):
    # VOICEVOXの無料WebAPIを利用して音声を生成
    # speaker_id 3 = ずんだもん（あまめ）、2 = 四国めたん、など
    # ここでは「カイ」っぽい落ち着いた男性声（四国めたん等の調整）を狙います
    print(f"VOICEVOXで音声生成中: {text[:20]}...")
    
    # 1. 音声合成用のクエリを作成
    query_url = f"https://voicevox-proxy.appspot.com/audio_query?text={text}&speaker={speaker_id}"
    query_res = requests.post(query_url)
    
    # 2. 音声データを生成
    synthesis_url = f"https://voicevox-proxy.appspot.com/synthesis?speaker={speaker_id}"
    voice_res = requests.post(synthesis_url, json=query_res.json())
    
    with open("voice.wav", "wb") as f:
        f.write(voice_res.content)

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=99"
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
    download_voicevox(script, speaker_id=2) # 2番は落ち着いた「めたん」の声
    make_video()
