import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip, AudioArrayClip
from pydub import AudioSegment, AudioOp

def get_horror_script(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{
                "text": """
                あなたは伝説の怪談師です。視聴者の耳元で囁くように語ってください。
                指示：文中に（笑い声）や（吐息）を入れ、人間らしい『タメ』を作ってください。
                冒頭：「…ねぇ、聞こえる？…これ、あなたの部屋の音じゃないよね？」
                最後：「…あ、後ろ。見ちゃだめだよ。…ふふっ。」
                Prompt: (不気味な画像生成用英語プロンプト)
                """
            }]
        }],
        "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}]
    }
    response = requests.post(url, json=payload)
    data = response.json()
    text = data['candidates'][0]['content']['parts'][0]['text']
    script = text.split("Prompt:")[0].strip()
    img_prompt = "Eerie cinematic horror, dark ambient " + (text.split("Prompt:")[1].strip() if "Prompt:" in text else "ghostly face in dark")
    return script, img_prompt

def download_voicevox(text, speaker_id=2):
    base_url = "http://localhost:50021"
    for _ in range(30):
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
    
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    query_data = query_res.json()
    query_data['speedScale'] = 0.85  # 落ち着いたトーン
    query_data['intonationScale'] = 1.6 # 感情を強調
    
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_data)
    with open("raw_voice.wav", "wb") as f:
        f.write(voice_res.content)

def process_audio():
    # 1. 音声の読み込み
    voice = AudioSegment.from_wav("raw_voice.wav")
    
    # 2. 【リバーブ加工】音声をわずかに重ねて残響を作る
    reverb = voice - 10  # 音量を下げた残響
    voice = voice.overlay(reverb, position=50).overlay(reverb, position=100)
    
    # 3. 【環境音の追加】
    # ここでは不気味な低音（ホワイトノイズを加工したもの）をシミュレート
    # 実際にはGitHubに 'ambient.mp3' を置いておけばそれを合成できます
    combined = voice.set_frame_rate(44100)
    combined.export("processed_voice.wav", format="wav")

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=666"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video():
    audio = AudioFileClip("processed_voice.wav")
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_horror_script(api_key)
    download_image(img_prompt)
    download_voicevox(script, speaker_id=2)
    process_audio()  # ここで音響加工
    make_video()
