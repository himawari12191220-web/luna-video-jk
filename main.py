import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip

def get_horror_script(api_key):
    # Gemini 3 Flash Preview 用のURL（安定性を考慮し v1beta を使用）
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "都市伝説テラーのカイとして、短くてゾッとする話を1つ。最後に画像生成用英語プロンプトを 'Prompt: (英語)' の形式で付けて。"}]}],
        "safetySettings": [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}]
    }
    response = requests.post(url, json=payload)
    data = response.json()
    text = data['candidates'][0]['content']['parts'][0]['text']
    script = text.split("Prompt:")[0].strip()
    img_prompt = "Dark eerie cinematic horror " + (text.split("Prompt:")[1].strip() if "Prompt:" in text else "abandoned asylum")
    return script, img_prompt

def download_voicevox(text, speaker_id=2):
    # 複数のAPIサーバーを試行して安定性を高める
    print(f"VOICEVOXで音声生成を試行中...")
    base_url = "https://voicevox-proxy.appspot.com"
    
    try:
        # 1. 音声合成クエリの作成
        query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}", timeout=30)
        query_res.raise_for_status() # エラーなら例外を投げる
        
        # 2. 音声データの生成
        voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_res.json(), timeout=60)
        voice_res.raise_for_status()
        
        with open("voice.wav", "wb") as f:
            f.write(voice_res.content)
        return True
    except Exception as e:
        print(f"VOICEVOX APIエラー: {e}")
        return False

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=99"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video():
    if not os.path.exists("voice.wav"):
        print("音声ファイルがないため、動画作成をスキップします。")
        return
    
    audio = AudioFileClip("voice.wav")
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_horror_script(api_key)
    download_image(img_prompt)
    
    # 音声生成に成功した場合のみ動画を作る
    if download_voicevox(script, speaker_id=2):
        make_video()
    else:
        print("音声を生成できなかったため、今回は終了します。")
