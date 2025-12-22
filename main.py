import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip
from pydub import AudioSegment

def get_horror_script(api_key):
    # Gemini 3 Flash の最新エンドポイント（アカウントの権限に合わせて最適化）
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": """
                あなたは伝説の怪談師です。視聴者が夜、一人でいることを後悔するような話を1つ語ってください。
                
                【Gemini 3 Flashへの演技指示】
                ・人間らしい『息遣い』や『間』を表現するため、文中に「（はぁ…）」「（ふふっ）」「（…っ！）」を入れてください。
                ・「…」を効果的に使い、じわじわと追い詰めるような話し方にしてください。
                ・冒頭は「…ねぇ、聞こえる？…これ、あなたの部屋の音じゃないよね？」
                ・最後は「…あ、後ろ。見ちゃだめだよ。…ふふっ。」
                
                【出力形式】
                物語の内容
                Prompt: (不気味で実写のような画像生成用英語プロンプト)
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
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        # 安全フィルター等で内容が空の場合の対策
        if 'candidates' not in data or not data['candidates'][0].get('content'):
            return "…ねぇ、後ろに誰かいない？…なんてね、通信エラーだよ。次はちゃんとしてね。", "Eerie dark hallway, cinematic lighting"

        text = data['candidates'][0]['content']['parts'][0]['text']
        # 台本と画像プロンプトを分離
        script = text.split("Prompt:")[0].strip()
        img_prompt = "Hyper-realistic horror, dark ambient, " + (text.split("Prompt:")[1].strip() if "Prompt:" in text else "ghostly shadow")
        return script, img_prompt
    except Exception as e:
        return "…システムに何かが入り込んだみたい。通信エラーだよ。", "Glitched digital ghost"

def download_voicevox(text, speaker_id=2):
    base_url = "http://localhost:50021"
    
    # エンジンの起動を待機
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
    
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    query_data = query_res.json()
    
    # 人間味のある音響設定
    query_data['speedScale'] = 0.85      # 少しゆっくり
    query_data['intonationScale'] = 1.7 # 抑揚（感情）を強く
    
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_data)
    with open("raw_voice.wav", "wb") as f:
        f.write(voice_res.content)

def process_audio():
    if not os.path.exists("raw_voice.wav"): return
    voice = AudioSegment.from_wav("raw_voice.wav")
    
    # 【リバーブ加工】
    reverb = voice - 15 
    processed = voice.overlay(reverb, position=60).overlay(reverb, position=120)
    processed.export("processed_voice.wav", format="wav")

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=999"
    res = requests.get(url)
    with open("background.jpg", 'wb') as f:
        f.write(res.content)

def make_video():
    audio_path = "processed_voice.wav" if os.path.exists("processed_voice.wav") else "raw_voice.wav"
    audio = AudioFileClip(audio_path)
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
