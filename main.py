import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script(api_key):
    # Gemini 3 Flash の最新エンドポイントを使用
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": """
                あなたは伝説の怪談師です。視聴者が夜、一人でいることを後悔するような話を1つ語ってください。
                
                【演技指導】
                ・文中に「（はぁ…）」「（ふふっ）」などの吐息や笑い声を入れ、人間らしい『タメ』を作ってください。
                ・冒頭は「…ねぇ、聞こえる？…これ、あなたの部屋の音じゃないよね？」
                ・最後は「…あ、後ろ。見ちゃだめだよ。…ふふっ。」
                
                【出力形式】
                物語の内容
                Prompt: (英語の画像プロンプト。不気味な廃墟や影を詳細に指示して)
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
        text = data['candidates'][0]['content']['parts'][0]['text']
        script = text.split("Prompt:")[0].strip()
        img_prompt = "Cinematic horror, 4k, " + (text.split("Prompt:")[1].strip() if "Prompt:" in text else "dark haunted room")
        return script, img_prompt
    except:
        return "…ねぇ、後ろに誰かいない？…なんてね、通信エラーだよ。", "Dark spooky house, cinematic horror"

def download_voicevox(text, speaker_id=2):
    base_url = "http://localhost:50021"
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
    
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    query_data = query_res.json()
    query_data['speedScale'] = 0.85
    query_data['intonationScale'] = 1.7
    
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_data)
    with open("raw_voice.wav", "wb") as f:
        f.write(voice_res.content)

def process_audio():
    if not os.path.exists("raw_voice.wav"): return
    voice = AudioSegment.from_wav("raw_voice.wav")
    reverb = voice - 15 
    processed = voice.overlay(reverb, position=60).overlay(reverb, position=120)
    processed.export("processed_voice.wav", format="wav")

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=13"
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open("background_raw.jpg", 'wb') as f:
                f.write(res.content)
            
            # 【重要】Pillowを使って画像を再保存し、形式を完全に整える
            with Image.open("background_raw.jpg") as img:
                img.convert("RGB").save("background.jpg", "JPEG")
            return True
    except Exception as e:
        print(f"Image Download Error: {e}")
    return False

def make_video():
    if not os.path.exists("background.jpg"):
        print("Error: background.jpg が生成されていません")
        return

    audio_path = "processed_voice.wav" if os.path.exists("processed_voice.wav") else "raw_voice.wav"
    audio = AudioFileClip(audio_path)
    
    # 画像の読み込み（再保存した確実なファイルを使用）
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_horror_script(api_key)
    
    # 画像ダウンロードと変換
    if download_image(img_prompt):
        download_voicevox(script, speaker_id=2)
        process_audio()
        make_video()
    else:
        print("画像のダウンロードに失敗したため中断します")
