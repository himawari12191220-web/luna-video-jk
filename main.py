import os
import requests
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings

# フォントの設定（Linux環境用）
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

def get_luna_script(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = """
    あなたは少し毒舌な女子高生『ルナ』です。
    視聴者が驚く『世界の真実・雑学』を1つ教えて。
    【ルール】
    ・冒頭は必ず「ねぇ、まだそんなこと信じてんの？」から始める。
    ・最後は「ま、知ったところでどうにもならないけどね」で締める。
    ・最後に、雑学に関連する画像生成用英語プロンプトを「Prompt: (英語)」の形式で出力して。
    """
    response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
    text = response.json()['candidates'][0]['content']['parts'][0]['text']
    
    script = text.split("Prompt:")[0].strip()
    img_prompt = text.split("Prompt:")[1].strip() if "Prompt:" in text else "Cyberpunk city"
    return script, img_prompt

def download_image(prompt):
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1080&height=1920&seed=42"
    with open("background.jpg", 'wb') as f:
        f.write(requests.get(url).content)

def make_video(script):
    tts = gTTS(script, lang='ja')
    tts.save("voice.mp3")
    audio = AudioFileClip("voice.mp3")
    
    clip = ImageClip("background.jpg").set_duration(audio.duration)
    # 字幕の設定（エラー回避のため標準フォントを使用）
    txt = TextClip(script, fontsize=50, color='white', method='caption', size=(900, None)).set_duration(audio.duration)
    
    video = CompositeVideoClip([clip, txt.set_position('center')])
    video.set_audio(audio).write_videofile("output.mp4", fps=24, codec="libx264")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    script, img_prompt = get_luna_script(api_key)
    download_image(img_prompt)
    make_video(script)
