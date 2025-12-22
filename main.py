import os
import requests
import time
import re
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeAudioClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script():
    # ngrokのURL（画像9の通り online であることを前提としています）
    NGROK_BASE_URL = "https://defectible-merilyn-debonairly.ngrok-free.dev/v1"
    
    payload = {
        "model": "hermes-3-llama-3.1-8b",
        "messages": [
            {
                "role": "system", 
                "content": "あなたはプロの怪談師です。余計な見出し（【本文】や1.など）や解説、注意書きは一切含めず、『怪談の本文』『Prompt』『BGM』の3要素だけを簡潔に出力してください。"
            },
            {
                "role": "user", 
                "content": "【出力形式を厳守】\n怪談の本文（日本語で150文字程度。見出し不要）\nPrompt: (英語の画像プロンプト)\nBGM: (slow, dark, tensionのいずれか1つ)"
            }
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{NGROK_BASE_URL}/chat/completions", json=payload, timeout=120)
        data = response.json()
        text = data['choices'][0]['message']['content']
        
        print(f"--- Raw AI Output ---\n{text}\n--------------------")

        # 【BGMの抽出】
        # テキスト全体からキーワードを検索（見出しがどうであれ判定可能にする）
        bgm_type = "slow"
        lower_text = text.lower()
        if "tension" in lower_text: bgm_type = "tension"
        elif "dark" in lower_text: bgm_type = "dark"
        elif "slow" in lower_text: bgm_type = "slow"

        # 【台本のクリーニング】
        # 1. Prompt: 以降を完全に切り捨てる
        script = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[0].strip()
        
        # 2. 余計なラベル（【本文】、1.、日本語の〜：など）を徹底排除
        script = re.sub(r'^.*?本文.*?[:：]\s*', '', script, flags=re.MULTILINE)
        script = re.sub(r'^[0-9]\.\s*', '', script, flags=re.MULTILINE)
        script = re.sub(r'【.*?】', '', script) # 【本文】などのカッコを消去
        script = re.sub(r'※.*$', '', script, flags=re.DOTALL) # 画像11にあった注意書きを削除
        
        script = script.strip()

        # 【画像プロンプトの抽出】
        img_prompt = "Dark eerie haunted house, cinematic"
        if "Prompt:" in text or "Prompt：" in text:
            # Prompt: と BGM: の間を抜き出す
            parts = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[1]
            img_prompt = re.split(r'BGM[:：]', parts, flags=re.IGNORECASE)[0].strip()
            img_prompt = re.sub(r'【.*?】', '', img_prompt).strip()

        return script, img_prompt, bgm_type
    except Exception as e:
        print(f"Script Error: {e}")
        return "…ねぇ。そこにいるのは分かっているよ。…ふふっ。", "Dark room silhouette", "slow"

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
    
    # BGMフォルダ内のファイル確認
    bgm_path = f"bgm/{bgm_type}.mp3"
    print(f"Applying BGM: {bgm_path}")
    
    if os.path.exists(bgm_path):
        # 画像8のファイル構成に合わせてBGMをミックス
        bgm_audio = AudioFileClip(bgm_path).volumex(0.12).set_duration(voice_audio.duration)
        final_audio = CompositeAudioClip([voice_audio, bgm_audio])
    else:
        print(f"Warning: BGM {bgm_path} not found.")
        final_audio = voice_audio

    if os.path.exists("background.jpg"):
        clip = ImageClip("background.jpg").set_duration(voice_audio.duration)
        clip = clip.resize(lambda t: 1 + 0.01 * t) # 背景ズーム
    else:
        clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(voice_audio.duration)
    
    video = clip.set_audio(final_audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    script, img_prompt, bgm_type = get_horror_script()
    print(f"--- Cleaned Result ---")
    print(f"Script: {script}")
    print(f"BGM: {bgm_type}")
    
    download_image(img_prompt)
    download_voicevox(script, speaker_id=2)
    process_audio()
    make_video(bgm_type)
