import os
import requests
import time
from moviepy.editor import ImageClip, AudioFileClip, ColorClip
from pydub import AudioSegment
from PIL import Image

def get_horror_script(api_key):
    # Gemini 3 Flash (1.5 Flash) の最新エンドポイントを使用
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": """
                あなたは一流の短編小説家です。読者が「日常のすぐ隣にある違和感」を感じてゾッとするような、150文字程度の不思議な体験談を書いてください。
                
                【執筆のルール】
                1. 直接的な暴力、流血、死、犯罪に関する言葉は「絶対に」使わないでください。AIの検閲を避けるためです。
                2. 「誰もいないはずなのに音がする」「鏡の中の自分が一瞬遅れて動いた」といった、静かな心理的恐怖をテーマにしてください。
                3. 文中に（ふふっ）（はぁ…）という演技指示を入れ、語り部としての体温を感じさせてください。
                4. 最後に必ず 'Prompt: (英語の幻想的で不気味な画像プロンプト)' を1行だけ付けてください。
                
                語り出し：「…ねぇ、聞こえる？…これ、あなたの部屋の音じゃないよね？」
                締めくくり：「…あ、後ろ。見ちゃだめだよ。…ふふっ。」
                """
            }]
        }],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        
        # 検閲でブロックされた場合の予備台本
        if 'candidates' not in data or not data['candidates'][0].get('content'):
            return "…ふふっ。まだ、あなたの後ろの影に気づいてないみたいだね。…怖い話、聞きたい？（はぁ…）いいよ、今夜だけ特別に教えてあげる。", "Eerie silhouette in a dark room, cinematic lighting"

        text = data['candidates'][0]['content']['parts'][0]['text']
        script = text.split("Prompt:")[0].strip()
        img_prompt = (text.split("Prompt:")[1].strip() if "Prompt:" in text else "Dark mysterious fog, cinematic lighting, horror")
        return script, img_prompt
    except:
        return "…不思議。影が一つ増えてる。…今日はもう、寝たほうがいいよ。", "Dark moody atmosphere, hyper-realistic"

def download_voicevox(text, speaker_id=2):
    base_url = "http://localhost:50021"
    # エンジンの起動を待機
    for _ in range(60):
        try:
            if requests.get(f"{base_url}/version").status_code == 200: break
        except: time.sleep(1)
    
    query_res = requests.post(f"{base_url}/audio_query?text={text}&speaker={speaker_id}")
    query_data = query_res.json()
    
    # 【人間らしさ・囁き声の極致設定】
    query_data['speedScale'] = 0.88      # 少しだけゆっくりして「溜め」を作る
    query_data['intonationScale'] = 1.8 # 抑揚を激しくして感情を乗せる
    query_data['volumeScale'] = 1.2    # 囁きでも聞き取りやすく調整
    
    voice_res = requests.post(f"{base_url}/synthesis?speaker={speaker_id}", json=query_data)
    with open("raw_voice.wav", "wb") as f:
        f.write(voice_res.content)

def process_audio():
    if not os.path.exists("raw_voice.wav"): return
    voice = AudioSegment.from_wav("raw_voice.wav")
    
    # 【リバーブ（残響）加工】
    # 広い廃墟で囁いているような質感を出すためにディレイを重ねる
    reverb = voice - 15 
    processed = voice.overlay(reverb, position=50).overlay(reverb, position=100)
    
    processed.export("processed_voice.wav", format="wav")

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed={int(time.time())}"
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            with open("temp.jpg", 'wb') as f: f.write(res.content)
            with Image.open("temp.jpg") as img: 
                img.convert("RGB").save("background.jpg", "JPEG")
            return True
    except: return False

def make_video():
    audio_path = "processed_voice.wav" if os.path.exists("processed_voice.wav") else "raw_voice.wav"
    if not os.path.exists(audio_path): return
    
    audio = AudioFileClip(audio_path)
    
    # 画像があれば使用、なければ黒背景（エラー防止）
    if os.path.exists("background.jpg"):
        clip = ImageClip("background.jpg").set_duration(audio.duration)
    else:
        clip = ColorClip(size=(1080, 1920), color=(0,0,0)).set_duration(audio.duration)
    
    video = clip.set_audio(audio)
    video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    
    print("1. Gemini 3 Flashで脚本を生成中...")
    script, img_prompt = get_horror_script(api_key)
    
    print("2. 不気味な背景を生成中...")
    download_image(img_prompt)
    
    print("3. VOICEVOXで囁き声を生成中...")
    download_voicevox(script, speaker_id=2)
    
    print("4. 音響加工（リバーブ）を適用中...")
    process_audio()
    
    print("5. 動画を書き出し中...")
    make_video()
    print("すべて完了しました。")
