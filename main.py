import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeAudioClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script():
    # あなたのngrok URL
    NGROK_BASE_URL = "https://defectible-merilyn-debonairly.ngrok-free.dev/v1"
    
    payload = {
        "model": "hermes-3-llama-3.1-8b",
        "messages": [
            {
                "role": "system", 
                "content": "あなたは日本のプロ怪談師です。必ず『日本語』で怪談を書いてください。文中に（はぁ…）（ふふっ）などの演技を入れて、視聴者を恐怖させてください。また、最後に必ず画像用の英語プロンプトとBGMの種類を添えてください。"
            },
            {
                "role": "user", 
                "content": "【重要：必ず日本語で出力してください】150文字程度のゾッとする怖い話を1つ。構成：1.日本語の怪談本文 2.Prompt: (英語の画像プロンプト) 3.BGM: (slow, dark, tensionのいずれか) の順で出力してください。"
            }
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{NGROK_BASE_URL}/chat/completions", json=payload, timeout=120)
        data = response.json()
        text = data['choices'][0]['message']['content']
        
        # 日本語が含まれていない場合の警告（ログ用）
        print(f"Generated Content: {text}")
        
        # BGMタイプの抽出
        bgm_type = "slow"
        if "bgm: dark" in text.lower(): bgm_type = "dark"
        elif "bgm: tension" in text.lower(): bgm_type = "tension"
        
        # 脚本、プロンプトの分離（Prompt: という単語を区切りにする）
        script = text.split("Prompt:")[0].strip()
        remaining = text.split("Prompt:")[1] if "Prompt:" in text else "Dark creepy room, cinematic"
        img_prompt = remaining.split("BGM:")[0].strip()
        
        return script, img_prompt, bgm_type
    except Exception as e:
        print(f"Script Error: {e}")
        return "…ねぇ。鏡の中のあなたが、ずっと笑ってるよ。…ふふっ。", "dark mirror, cinematic", "slow"

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
    
    # BGMの読み込みと合成（ファイル名は小文字で指定）
    bgm_path = f"bgm/{bgm_type}.mp3"
    if os.path.exists(bgm_path):
        bgm_audio = AudioFileClip(bgm_path).volumex(0.15).set_duration(voice_audio.duration)
        final_audio = CompositeAudioClip([voice_audio, bgm_audio])
    else:
        final_audio = voice_audio

    # 背景動画化（ゆっくりズーム）
    if os.path.exists("background.jpg"):
        clip = ImageClip("background.jpg").set_duration(voice_audio.duration)
        clip = clip.resize(lambda t: 1 + 0.01 * t) 
    else:
        clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(voice_audio.duration)
    
    video = clip.set_audio(final_audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    print("--- 生成開始 ---")
    script, img_prompt, bgm_type = get_horror_script()
    print(f"BGM Type: {bgm_type}")
    
    download_image(img_prompt)
    download_voicevox(script, speaker_id=2)
    process_audio()
    make_video(bgm_type)
    print("--- すべて完了 ---")
