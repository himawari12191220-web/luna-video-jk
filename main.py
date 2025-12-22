import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip
from pydub import AudioSegment

def get_horror_script(api_key):
    # Gemini 3 Flash の最新エンドポイントを使用
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": """
                あなたは伝説の怪談師です。視聴者が夜、一人でいることを後悔するような話を1つ語ってください。
                
                【演技指導】
                ・人間らしい『息遣い』や『間』を表現するため、文中に「（はぁ…）」「（ふふっ）」「（…っ！）」を入れてください。
                ・「…」を効果的に使い、じわじわと追い詰めるような話し方にしてください。
                ・冒頭は「…ねぇ、聞こえる？…これ、あなたの部屋の音じゃないよね？」
                ・最後は「…あ、後ろ。見ちゃだめだよ。…ふふっ。」
                
                【出力形式】
                物語の内容
                Prompt: (不気味で実写のような、霧がかった廃墟の英語画像プロンプト)
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
        
        if 'candidates' not in data or not data['candidates'][0].get('content'):
            return "…ねぇ、後ろに誰かいない？…なんてね、通信エラーだよ。", "Dark spooky house, mist, cinematic horror"

        text = data['candidates'][0]['content']['parts'][0]['text']
        script = text.split("Prompt:")[0].strip()
        img_prompt = "Cinematic horror, dark ambient lighting, " + (text.split("Prompt:")[1].strip() if "Prompt:" in text else "haunted dark forest")
        return script, img_prompt
    except:
        return "…システムに何かが入り込んだみたい。通信エラーだよ。", "Glitched digital ghost"

def download_voicevox(text, speaker_id=2):
    base_url = "http://localhost:50021"
    # VOICEVOXエンジンの起動待ち
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
    
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    query_data = query_res.json()
    query_data['speedScale'] = 0.85      # ゆっくり落ち着いたトーン
    query_data['intonationScale'] = 1.7 # 抑揚を強くして感情を出す
    
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_data)
    with open("raw_voice.wav", "wb") as f:
        f.write(voice_res.content)

def process_audio():
    if not os.path.exists("raw_voice.wav"): return
    voice = AudioSegment.from_wav("raw_voice.wav")
    
    # 【リバーブ加工】深い残響を加えて廃墟感を出す
    reverb = voice - 15 
    processed = voice.overlay(reverb, position=60).overlay(reverb, position=120)
    processed.export("processed_voice.wav", format="wav")

def download_image(prompt):
    # 画像生成。確実な読み込みのためリトライを追加
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=13"
    for _ in range(3):
        res = requests.get(url)
        if res.status_code == 200:
            with open("background.jpg", 'wb') as f:
                f.write(res.content)
            return True
        time.sleep(2)
    return False

def make_video():
    # ファイル存在確認
    if not os.path.exists("background.jpg"):
        print("Error: background.jpg が見つかりません")
        return

    audio_path = "processed_voice.wav" if os.path.exists("processed_voice.wav") else "raw_voice.wav"
    audio = AudioFileClip(audio_path)
    
    # 画像の読み込み（エラー回避のために明示的に読み込む）
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_horror_script(api_key)
    if download_image(img_prompt):
        download_voicevox(script, speaker_id=2)
        process_audio()
        make_video()
