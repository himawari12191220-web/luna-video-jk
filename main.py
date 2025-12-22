import os
import requests
import time
import re
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeAudioClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script():
    NGROK_BASE_URL = "https://defectible-merilyn-debonairly.ngrok-free.dev/v1"
    
    payload = {
        "model": "hermes-3-llama-3.1-8b",
        "messages": [
            {
                "role": "system", 
                "content": "あなたはプロの怪談師です。余計なラベルや解説は一切含めず、怪談の本文、Prompt、BGMのみを簡潔に出力してください。"
            },
            {
                "role": "user", 
                "content": "【出力形式】\n怪談の本文（日本語で150文字程度。※『1.本文：』などの見出しは不要です）\nPrompt: (英語の画像プロンプト)\nBGM: (slow, dark, tensionのいずれか1つ)"
            }
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{NGROK_BASE_URL}/chat/completions", json=payload, timeout=120)
        data = response.json()
        text = data['choices'][0]['message']['content']
        
        print(f"--- Raw AI Output ---\n{text}\n--------------------")

        # 【BGM判定の超強化】
        # 文章の中に特定のニュアンスが含まれていれば、自動でファイル名に変換する
        lower_text = text.lower()
        bgm_type = "slow" # デフォルト
        
        if any(w in lower_text for w in ["tension", "不気味な音楽", "激しい", "緊迫", "追いかけ"]):
            bgm_type = "tension"
        elif any(w in lower_text for w in ["dark", "重苦しい", "地響き", "怨嗟", "深淵"]):
            bgm_type = "dark"
        elif any(w in lower_text for w in ["slow", "静か", "ピアノ", "孤独", "囁き"]):
            bgm_type = "slow"

        # 【台本の徹底クリーニング】
        # Prompt: 以降は台本に含めない
        script = text.split("Prompt:")[0].strip()
        
        # 不要な見出し（1. 本文、BGM、※など）を削除する正規表現
        script = re.sub(r"^[0-9]\.?\s*", "", script)
        script = re.sub(r"^.*?怪談.*?[:：]\s*", "", script, flags=re.MULTILINE)
        script = re.sub(r"^.*?本文[:：]\s*", "", script, flags=re.MULTILINE)
        script = re.sub(r"^.*?BGM[:：].*$", "", script, flags=re.MULTILINE) # BGM説明行を削除
        script = re.sub(r"※.*$", "", script, flags=re.DOTALL) # 注意書き削除
        
        # 「夜空に浮かぶ月は…音楽が響く」のようなBGM説明文が文末にある場合を考慮し削除
        script = re.sub(r"BGM.*$", "", script, flags=re.IGNORECASE | re.DOTALL).strip()

        # 画像プロンプトの抽出
        img_prompt = "Eerie forest blood moon, cinematic horror"
        if "Prompt:" in text:
            img_prompt = text.split("Prompt:")[1].split("BGM:")[0].strip()
            img_prompt = re.sub(r"^[0-9]\.\s*", "", img_prompt)

        return script, img_prompt, bgm_type
    except Exception as e:
        print(f"Script Error: {e}")
        return "…ねぇ。そこにいるんでしょ？…ふふっ。", "Dark forest blood moon", "slow"

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
    
    # BGMの選択と合成
    bgm_path = f"bgm/{bgm_type}.mp3"
    print(f"System decided to use: {bgm_path}")
    
    if os.path.exists(bgm_path):
        bgm_audio = AudioFileClip(bgm_path).volumex(0.12).set_duration(voice_audio.duration)
        final_audio = CompositeAudioClip([voice_audio, bgm_audio])
    else:
        print(f"Warning: {bgm_path} not found. Check your bgm folder.")
        final_audio = voice_audio

    if os.path.exists("background.jpg"):
        clip = ImageClip("background.jpg").set_duration(voice_audio.duration)
        clip = clip.resize(lambda t: 1 + 0.01 * t)
    else:
        clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(voice_audio.duration)
    
    video = clip.set_audio(final_audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    script, img_prompt, bgm_type = get_horror_script()
    print(f"Final Cleaned Script: {script}")
    
    download_image(img_prompt)
    download_voicevox(script, speaker_id=2)
    process_audio()
    make_video(bgm_type)
