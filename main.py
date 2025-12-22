import os
import requests
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip

# 1. 脳（Gemini）への指示：毒舌女子高生になりきらせる
def get_luna_script(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = """
    あなたは少し毒舌な女子高生『ルナ』です。
    視聴者が驚く『世界の真実・雑学』を1つ教えて。
    【ルール】
    ・冒頭は必ず「ねぇ、まだそんなこと信じてんの？」や「マジか、知らないの？」から始める。
    ・口調は女子高生。最後に少し冷たい一言を添える。
    ・全体で40秒以内の音声になる長さ。
    ・最後に、その雑学に関連する英語の画像生成プロンプトを1つ出力して。
    """
    
    response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
    # ここでテキストと画像用プロンプトに分割する処理
    result = response.json()['candidates'][0]['content']['parts'][0]['text']
    return result

# 2. 絵描き（Pollinations）：毒舌JKに合う背景を作る
def get_luna_image(img_prompt):
    # 常に「アニメ調の女子高生の部屋」などを背景に混ぜる
    full_prompt = f"Anime style, cynical school girl, dark room, {img_prompt}"
    url = f"https://pollinations.ai/p/{full_prompt}?width=1080&height=1920"
    return requests.get(url).content

# 3. 編集（MoviePy）：声と絵を合体させて動画にする
# (※前回のコードをベースに、ルナの性格に合わせて字幕の色を「ショッキングピンク」などに設定します)