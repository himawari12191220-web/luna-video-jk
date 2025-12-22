import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip
from pydub import AudioSegment

def get_horror_script(api_key):
    # Gemini 3 Flash Preview を使用
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": """
                あなたは伝説の怪談師です。視聴者の耳元で囁くように語ってください。
                
                【表現の指示】
                ・文中に「（はぁ…）」「（ふふっ）」などの吐息や笑い声を入れ、人間らしい『タメ』を作ってください。
                ・冒頭は「…ねぇ、聞こえる？…これ、あなたの部屋の音じゃないよね？」
                ・最後は「…あ、後ろ。見ちゃだめだよ。…ふふっ。」
                
                【出力形式】
                物語の内容
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
    # エンジンの起動を待機
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/version").status_code == 200:
                break
        except:
            time.sleep(1)
    
    # クエリ作成（人間味のあるパラメータ調整）
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    query_data = query_res.json()
    query_data['speedScale'] = 0.85      # 少しゆっくり
    query_data['intonationScale'] = 1.6 # 抑揚を強める
    
    # 音声合成
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_data)
    with open("raw_voice.wav", "wb") as f:
        f.write(voice_res.content)

def process_audio():
    # pydubを使用してリバーブと環境音を加工
    voice = AudioSegment.from_wav("raw_voice.wav")
    
    # 【リバーブ加工】音をわずかに遅らせて重ねることで残響を作る
    reverb = voice - 12  # 音量を下げた影の音
    # 50msと100msの遅延を重ねて「広い部屋」感を出す
    processed = voice.overlay(reverb, position=50).overlay(reverb, position=100)
    
    # 最終的な音声ファイルとして書き出し
    processed.export("processed_voice.wav", format="wav")

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=666"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video():
    # 加工後の音声を使用
    audio = AudioFileClip("processed_voice.wav")
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    # 1. シナリオ生成
    script, img_prompt = get_horror_script(api_key)
    # 2. 画像ダウンロード
    download_image(img_prompt)
    # 3. 音声生成(VOICEVOX)
    download_voicevox(script, speaker_id=2)
    # 4. 音響加工(リバーブ等)
    process_audio()
    # 5. 動画合成
    make_video()
