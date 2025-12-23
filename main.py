import os
import requests
import time
import re
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, CompositeAudioClip, TextClip, CompositeVideoClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script():
    # 固定ドメイン URL
    NGROK_BASE_URL = "https://defectible-merilyn-debonairly.ngrok-free.dev/v1"
    
    payload = {
        "model": "hermes-3-llama-3.1-8b",
        "messages": [
            {
                "role": "system", 
                "content": "あなたは毒舌女子高生『ルナ』です。冷酷な口調で怪談を語ります。必ず【本文】【Prompt】【BGM】の3項目を出力してください。"
            },
            {
                "role": "user", 
                "content": "【形式厳守】\n本文: 日本語の怪談（150文字程度。演技指示を入れること）\nPrompt: (英語の画像プロンプト)\nBGM: (slow, dark, tensionのいずれか)"
            }
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(f"{NGROK_BASE_URL}/chat/completions", json=payload, timeout=120)
        if response.status_code != 200:
            return "…ねぇ、接続エラー。バカなの？（はぁ…）", "glitch art", "slow"
            
        data = response.json()
        text = data['choices'][0]['message']['content']
        print(f"--- AI Output ---\n{text}")

        # BGM判定
        bgm_type = "slow"
        if "tension" in text.lower(): bgm_type = "tension"
        elif "dark" in text.lower(): bgm_type = "dark"

        # 台本の抽出とクリーニング
        script = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[0]
        script = re.sub(r'【.*?】|^.*?本文.*?[:：]\s*|^[0-9]\.\s*', '', script, flags=re.MULTILINE)
        script = re.sub(r'※.*$', '', script, flags=re.DOTALL)
        script = script.strip()

        # プロンプトの抽出
        img_prompt = "Eerie horror atmosphere, cinematic"
        if "Prompt:" in text or "Prompt：" in text:
            parts = re.split(r'Prompt[:：]', text, flags=re.IGNORECASE)[1]
            img_prompt = re.split(r'BGM[:：]', parts, flags=re.IGNORECASE)[0].strip()

        return script, img_prompt, bgm_type
    except Exception as e:
        print(f"Error: {e}")
        return "…そこにいるのはわかってるわよ。でも今は繋がらないみたいね。", "dark room silhouette", "slow"

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

def make_video(script, bgm_type):
    voice_path = "raw_voice.wav"
    if not os.path.exists(voice_path): return
    
    voice_audio = AudioFileClip(voice_path)
    
    # BGM合成
    bgm_path = f"bgm/{bgm_type}.mp3"
    if os.path.exists(bgm_path):
        bgm_audio = AudioFileClip(bgm_path).volumex(0.12).set_duration(voice_audio.duration)
        final_audio = CompositeAudioClip([voice_audio, bgm_audio])
    else:
        final_audio = voice_audio

    # 背景設定
    if os.path.exists("background.jpg"):
        bg_clip = ImageClip("background.jpg").set_duration(voice_audio.duration)
        bg_clip = bg_clip.resize(lambda t: 1 + 0.01 * t) # ズーム
    else:
        bg_clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(voice_audio.duration)

    # 【新機能】字幕（テロップ）の作成
    # 30文字ごとに改行を入れる処理
    wrapped_text = "\n".join([script[i:i+15] for i in range(0, len(script), 15)])
    
    txt_clip = TextClip(
        wrapped_text,
        fontsize=70,
        color='red',
        font='DejaVu-Sans-Bold', # GitHub Actions標準フォント
        stroke_color='black',
        stroke_width=2,
        method='caption',
        size=(900, None)
    ).set_start(0).set_duration(voice_audio.duration).set_position(('center', 800))

    # 映像と字幕を合成
    video = CompositeVideoClip([bg_clip, txt_clip])
    video = video.set_audio(final_audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    script, img_prompt, bgm_type = get_horror_script()
    download_image(img_prompt)
    download_voicevox(script, speaker_id=2)
    make_video(script, bgm_type)
