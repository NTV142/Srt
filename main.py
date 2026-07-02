import datetime
import re
import os
from ytmusicapi import YTMusic

def extract_video_id(input_str):
    input_str = input_str.strip()
    regex = r'(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/watch\?v=|\/watch\?.+&v=)([^#\&\?]{11})'
    match = re.search(regex, input_str)
    return match.group(1) if match else (input_str if len(input_str) == 11 else None)

def format_lrc_time(ms):
    if ms is None or ms < 0: ms = 0
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    milliseconds = ms % 1000
    return f"[{minutes:02}:{seconds:02}.{milliseconds:03}]"

def main():
    target_input = os.environ.get("YTM_URL", "").strip()
    delay_sec_str = os.environ.get("DELAY_SEC", "0").strip()
    
    try:
        delay_ms = int(float(delay_sec_str) * 1000)
    except ValueError:
        delay_ms = 0

    if not target_input:
        print("環境変数 YTM_URL がありません。")
        return

    video_id = extract_video_id(target_input)
    if not video_id:
        print("ビデオIDが不正です。")
        return

    yt = YTMusic()
    
    try:
        watch_playlist = yt.get_watch_playlist(videoId=video_id)
        lyrics_browse_id = watch_playlist.get("lyrics")
        if not lyrics_browse_id:
            return
            
        lyrics_data = yt.get_lyrics(browseId=lyrics_browse_id)
        lrc_content = ""
        
        if isinstance(lyrics_data, dict) and "lyrics" in lyrics_data and isinstance(lyrics_data["lyrics"], list):
            lines = lyrics_data["lyrics"]
            for line in lines:
                if isinstance(line, dict):
                    start_ms = line.get("start_time", 0) + delay_ms
                    text = line.get("text", "")
                else:
                    start_ms = delay_ms
                    text = str(line)
                lrc_content += f"{format_lrc_time(start_ms)}{text}\n"
        else:
            text_data = lyrics_data.get("lyrics", "") if isinstance(lyrics_data, dict) else str(lyrics_data)
            lines = [l.strip() for l in str(text_data).split("\n") if l.strip()]
            for i, line_text in enumerate(lines):
                start_ms = (i * 3000) + delay_ms
                lrc_content += f"{format_lrc_time(start_ms)}{line_text}\n"

        html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>YTM Lyrics Result</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #fafafa; color: #333; }}
        .box {{ max-width: 600px; margin: 0 auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
        h2 {{ margin-top: 0; font-size: 1.3rem; text-align: center; }}
        textarea {{ width: 100%; height: 400px; font-family: monospace; padding: 12px; margin-top: 10px; box-sizing: border-box; border: 1px solid #ddd; background: #f9f9f9; }}
        .back-btn {{ display: block; text-align: center; margin-top: 15px; color: #007bff; text-decoration: none; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="box">
        <h2>取得完了</h2>
        <p>以下のLRCテキストをコピーして使用してください。</p>
        <textarea readonly>{lrc_content}</textarea>
        <a class="back-btn" href="./index.html">⬅ 入力画面に戻る</a>
    </div>
</body>
</html>"""
        
        # 既存のindex.htmlを壊さないように、結果は result.html に書き出す
        with open("result.html", "w", encoding="utf-8") as f:
            f.write(html_template)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
