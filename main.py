import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeAudioClip
from pydub import AudioSegment

def get_horror_script(api_key):
    # 最新の Gemini 1.5 Flash エンドポイント（Gemini 3 Flashと互換性あり）
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": """
                あなたは伝説の怪談師です。視聴者の耳元で囁くように語ってください。
                
                【表現の指示】
                ・文中に「（はぁ…）」「（ふふっ）」などの吐息や笑い声を入れ、人間らしい『タメ』を作ってください。
                ・冒頭は「…ねぇ、聞こえる？…これ、あなたの部屋の音じゃないよね？」
                ・最後は「…あ、後ろ。見ちゃだめだよ。…ふふっ。」
                
                【出力形式】
                物語の内容
                Prompt: (不気味な画像生成用英語プロンプト)
                """
            }]
        }],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    # 【エラー対策】データがあるか厳重にチェック
    if 'candidates' not in data or not data['candidates'][0].get('content'):
        print("API Response Error:", data)
        return "…ねぇ、後ろに誰かいない？…なんてね、通信エラーだよ。", "Dark spooky ghost in a hallway"

    text = data['candidates'][0]['content']['parts'][0]['text']
    script = text.split("Prompt:")[0].strip()
    img_prompt = "Eerie cinematic horror masterwork, " + (text.split("Prompt:")[1].strip() if "Prompt:" in text else "dark haunted room")
    return script, img_prompt

def download_voicevox(text, speaker_id=2):
    base_url = "http://localhost:50021"
    for _ in range(60): # 起動待ち
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
    
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    query_data = query_res.json()
    query_data['speedScale'] = 0.85      # 落ち着いたトーン
    query_data['intonationScale'] = 1.6 # 抑揚を強く
    
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_data)
    with open("raw_voice.wav", "wb") as f:
        f.write(voice_res.content)

def process_audio():
    # pydubでリバーブ（残響）を加工
    voice = AudioSegment.from_wav("raw_voice.wav")
    
    # 【リバーブ】幽霊のような響きを作る
    reverb = voice - 15 
    processed = voice.overlay(reverb, position=60).overlay(reverb, position=120)
    
    # 最終音声
    processed.export("processed_voice.wav", format="wav")

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=444"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video():
    # 動画合成
    audio = AudioFileClip("processed_voice.wav")
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_horror_script(api_key)
    download_image(img_prompt)
    download_voicevox(script, speaker_id=2)
    process_audio()
    make_video()
