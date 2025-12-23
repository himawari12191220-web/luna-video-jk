import os
import requests
import time
import re
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeAudioClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script():
    # 固定ドメインを設定済み
    NGROK_BASE_URL = "https://defectible-merilyn-debonairly.ngrok-free.dev/v1"
    
    payload = {
        "model": "hermes-3-llama-3.1-8b",
        "messages": [
            {
                "role": "system", 
                "content": "あなたは毒舌な女子高生『ルナ』です。視聴者を突き放すような冷たい口調で怪談を語ります。余計な解説や見出し（1. 本文など）は一切含めず、本文、Prompt、BGMのみを出力してください。"
            },
            {
                "role": "user", 
                "content": "【出力形式】\n日本語の怪談（150文字程度。文中に『ふふっ』等の演技指示を入れること）\nPrompt: (英語の画像プロンプト)\nBGM: (slow, dark, tensionのいずれか)"
            }
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{NGROK_BASE_URL}/chat/completions", json=payload, timeout=120)
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return "…ねぇ。設定ミスってるわよ？バカなの？（はぁ…）", "glitch horror", "slow"
            
        data = response.json()
        text = data['choices'][0]['message']['content']
        print(f"--- Raw AI Output ---\n{text}\n--------------------")

        # BGM判定
        bgm_type = "slow"
        lower_text = text.lower()
        if "tension" in lower_text: bgm_type = "tension"
        elif "dark" in lower_text: bgm_type = "dark"

        # 台本のクリーニング（画像11, 12の不要なラベル【本文】や1.などを消去）
        script = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[0].strip()
        script = re.sub(r'【.*?】|^.*?本文.*?[:：]\s*|^[0-9]\.\s*', '', script, flags=re.MULTILINE)
        script = re.sub(r'※.*$', '', script, flags=re.DOTALL) 
        script = script.strip()

        # 画像プロンプトの抽出
        img_prompt = "Eerie horror atmosphere, cinematic"
        if "Prompt:" in text or "Prompt：" in text:
            parts = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[1]
            img_prompt = re.split(r'BGM[:：]', parts, flags=re.IGNORECASE)[0].strip()
            img_prompt = re.sub(r'【.*?】', '', img_prompt).strip()

        return script, img_prompt, bgm_type
    except Exception as e:
        print(f"Connection Failed: {e}")
        return "…そこにいるのはわかってるわよ。でも今は通信が繋がらないみたいね。", "dark room silhouette", "slow"

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed={int(time.time())}"
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open("temp.jpg", 'wb') as f: f.write(res.content)
            with Image.open("temp.jpg") as img: img.convert("RGB").save("background.jpg", "JPEG")
            return True
    except: return False

def download_voicevox(text, speaker_id=2):
    base_url = "http://localhost:50021"
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
    
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    query_data = query_res.json()
    query_data['speedScale'] = 0.88 
    query_data['intonationScale'] = 1.9
    
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_data)
    with open("raw_voice.wav", "wb") as f: f.write(voice_res.content)

def process_audio():
    if not os.path.exists("raw_voice.wav"): return
    voice = AudioSegment.from_wav("raw_voice.wav")
    reverb = voice - 15 
    processed = voice.overlay(reverb, position=50).overlay(reverb, position=100)
    processed.export("processed_voice.wav", format="wav")

def make_video(bgm_type):
    voice_path = "processed_voice.wav" if os.path.exists("processed_voice.wav") else "raw_voice.wav"
    if not os.path.exists(voice_path): return
    
    voice_audio = AudioFileClip(voice_path)
    
    # BGMの読み込み（画像8の構成に対応）
    bgm_path = f"bgm/{bgm_type}.mp3"
    if os.path.exists(bgm_path):
        bgm_audio = AudioFileClip(bgm_path).volumex(0.12).set_duration(voice_audio.duration)
        final_audio = CompositeAudioClip([voice_audio, bgm_audio])
    else:
        print(f"BGM未検出: {bgm_path}")
        final_audio = voice_audio

    # 背景のズーム演出
    if os.path.exists("background.jpg"):
        clip = ImageClip("background.jpg").set_duration(voice_audio.duration)
        clip = clip.resize(lambda t: 1 + 0.01 * t) 
    else:
        clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(voice_audio.duration)
    
    video = clip.set_audio(final_audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    print("--- LUNA SYSTEM START ---")
    script, img_prompt, bgm_type = get_horror_script()
    print(f"Script: {script}")
    print(f"BGM: {bgm_type}")
    
    download_image(img_prompt)
    download_voicevox(script, speaker_id=2)
    process_audio()
    make_video(bgm_type)
    print("--- COMPLETED ---")
