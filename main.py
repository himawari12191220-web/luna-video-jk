import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeAudioClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script():
    # あなたの最新のngrok URLです
    NGROK_BASE_URL = "https://defectible-merilyn-debonairly.ngrok-free.dev/v1"
    
    payload = {
        "model": "hermes-3-llama-3.1-8b",
        "messages": [
            {
                "role": "system", 
                "content": "あなたは一流の怪談師です。ゾッとする短編ホラーを書き、最後にその話に合うBGMの指定（slow/dark/tensionのどれか1つ）を 'BGM: [種類]' の形式で追加してください。"
            },
            {
                "role": "user", 
                "content": "150文字程度の怖い話。最後に必ず 'Prompt: (英語プロンプト)' と 'BGM: (種類)' を付けて。"
            }
        ],
        "temperature": 0.8
    }
    
    try:
        response = requests.post(f"{NGROK_BASE_URL}/chat/completions", json=payload, timeout=120)
        data = response.json()
        text = data['choices'][0]['message']['content']
        
        # BGM指定の抽出
        bgm_type = "slow"
        if "bgm: dark" in text.lower(): bgm_type = "dark"
        elif "bgm: tension" in text.lower(): bgm_type = "tension"
        
        script = text.split("Prompt:")[0].strip()
        # プロンプトとBGM指定を分離
        remaining = text.split("Prompt:")[1] if "Prompt:" in text else "dark horror ambient"
        img_prompt = remaining.split("BGM:")[0].strip()
        
        return script, img_prompt, bgm_type
    except Exception as e:
        print(f"Script Error: {e}")
        return "…ねぇ。鏡の中のあなたが笑ってるよ。", "dark horror mirror", "slow"

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
    with open("raw_voice.wav", "wb") as f:
        f.write(voice_res.content)

def process_audio():
    if not os.path.exists("raw_voice.wav"): return
    voice = AudioSegment.from_wav("raw_voice.wav")
    reverb = voice - 15 
    processed = voice.overlay(reverb, position=50).overlay(reverb, position=100)
    processed.export("processed_voice.wav", format="wav")

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed={int(time.time())}"
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open("temp.jpg", 'wb') as f:
                f.write(res.content)
            with Image.open("temp.jpg") as img:
                img.convert("RGB").save("background.jpg", "JPEG")
            return True
    except:
        return False

def make_video(bgm_type):
    voice_path = "processed_voice.wav" if os.path.exists("processed_voice.wav") else "raw_voice.wav"
    if not os.path.exists(voice_path): return
    
    voice_audio = AudioFileClip(voice_path)
    
    # 【BGM合成】bgm/ フォルダ内の指定されたファイルを使用
    bgm_file = f"bgm/{bgm_type}.mp3"
    if os.path.exists(bgm_file):
        bgm_audio = AudioFileClip(bgm_file).volumex(0.15) # 音量を15%に
        bgm_audio = bgm_audio.set_duration(voice_audio.duration)
        final_audio = CompositeAudioClip([voice_audio, bgm_audio])
    else:
        final_audio = voice_audio

    # 【背景動画化（ズーム効果）】
    if os.path.exists("background.jpg"):
        # 画像を読み込み、音声の長さに合わせてゆっくりズームさせる
        clip = ImageClip("background.jpg").set_duration(voice_audio.duration)
        # 1秒ごとに0.5%ずつ拡大（自然な動き）
        clip = clip.resize(lambda t: 1 + 0.005 * t) 
    else:
        clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(voice_audio.duration)
    
    video = clip.set_audio(final_audio)
    # 書き出し（YouTubeショート/TikTok向け）
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    print("1. 脚本を取得中...")
    script, img_prompt, bgm_type = get_horror_script()
    
    print("2. 画像を生成中...")
    download_image(img_prompt) # ここで定義した関数を正しく呼び出し
    
    print("3. 音声を生成中...")
    download_voicevox(script, speaker_id=2)
    
    print("4. 音響加工中...")
    process_audio()
    
    print("5. 動画を書き出し中（BGM合成とズーム適用）...")
    make_video(bgm_type)
    print("完了！")
