import os
import requests
import time
import random
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
        if "BGM: dark" in text.lower(): bgm_type = "dark"
        elif "BGM: tension" in text.lower(): bgm_type = "tension"
        
        script = text.split("Prompt:")[0].strip()
        img_prompt = text.split("Prompt:")[1].split("BGM:")[0].strip() if "Prompt:" in text else "dark horror ambient"
        
        return script, img_prompt, bgm_type
    except:
        return "…ねぇ。聞こえる？", "dark horror", "slow"

# (download_voicevox, process_audio, download_image は変更なしなので中略)

def make_video(bgm_type):
    voice_path = "processed_voice.wav" if os.path.exists("processed_voice.wav") else "raw_voice.wav"
    voice_audio = AudioFileClip(voice_path)
    
    # 【BGM合成のロジック】
    bgm_file = f"bgm/{bgm_type}.mp3"
    if os.path.exists(bgm_file):
        bgm_audio = AudioFileClip(bgm_file).volumex(0.15) # BGMは音量を15%に下げる
        # 音声の長さに合わせてBGMをカットまたはループ
        bgm_audio = bgm_audio.set_duration(voice_audio.duration)
        # 声とBGMをミックス
        final_audio = CompositeAudioClip([voice_audio, bgm_audio])
    else:
        final_audio = voice_audio

    # 【背景を動かす（ズーム効果）】
    if os.path.exists("background.jpg"):
        # 画像を動画として読み込み、ゆっくり1.1倍にズームさせる
        clip = ImageClip("background.jpg").set_duration(voice_audio.duration)
        clip = clip.resize(lambda t: 1 + 0.02*t) # 1秒ごとに2%ずつズーム
    else:
        clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(voice_audio.duration)
    
    video = clip.set_audio(final_audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    script, img_prompt, bgm_type = get_horror_script()
    download_image(img_prompt)
    download_voicevox(script, speaker_id=2)
    process_audio()
    make_video(bgm_type)
