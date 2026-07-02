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
    """ミリ秒を [分:秒.ミリ秒] 形式に変換 (ミリ秒は3桁)"""
    if ms is None or ms < 0: ms = 0
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    milliseconds = ms % 1000
    return f"[{minutes:02}:{seconds:02}.{milliseconds:03}]"

def main():
    target_input = os.environ.get("YTM_URL", "").strip()
    if not target_input:
        print("エラー: YTM_URL が指定されていません。")
        return

    video_id = extract_video_id(target_input)
    if not video_id:
        print("エラー: 有効なビデオIDが見つかりません。")
        return

    print(f"Target Video ID: {video_id}")
    yt = YTMusic()
    
    try:
        print("プレイリスト情報を取得中...")
        watch_playlist = yt.get_watch_playlist(videoId=video_id)
        lyrics_browse_id = watch_playlist.get("lyrics")
        if not lyrics_browse_id:
            print("エラー: 歌詞データが存在しません。")
            return
            
        print(f"歌詞データを要求中...")
        lyrics_data = yt.get_lyrics(browseId=lyrics_browse_id)
        
        lrc_content = ""
        
        # パターン1: タイムスタンプ付き
        if isinstance(lyrics_data, dict) and "lyrics" in lyrics_data and isinstance(lyrics_data["lyrics"], list):
            lines = lyrics_data["lyrics"]
            for line in lines:
                if isinstance(line, dict):
                    start_ms = line.get("start_time", 0)
                    text = line.get("text", "")
                else:
                    start_ms = 0
                    text = str(line)
                lrc_content += f"{format_lrc_time(start_ms)}{text}\n"
        
        # パターン2: プレーンテキスト（3秒ごとに分割）
        else:
            text_data = lyrics_data.get("lyrics", "") if isinstance(lyrics_data, dict) else str(lyrics_data)
            lines = [l.strip() for l in str(text_data).split("\n") if l.strip()]
            for i, line_text in enumerate(lines):
                start_ms = i * 3000
                lrc_content += f"{format_lrc_time(start_ms)}{line_text}\n"

        if not lrc_content.strip():
            print("エラー: 歌詞テキストがありませんでした。")
            return

        # 成果物（lyrics.srtのファイル名の中身をLRC形式で上書き保存します）
        with open("lyrics.srt", "w", encoding="utf-8") as f:
            f.write(lrc_content)
        
        html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>YTM Lyrics Result</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f5f5f5; }}
        .box {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        textarea {{ width: 100%; height: 400px; font-family: monospace; padding: 10px; margin-top: 10px; box-sizing: border-box; white-space: pre; }}
    </style>
</head>
<body>
    <div class="box">
        <h2>取得完了 (ID: {video_id})</h2>
        <p>以下のテキストをコピーして使用してください。</p>
        <textarea readonly>{lrc_content}</textarea>
    </div>
</body>
</html>"""
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_template)
            
        print("処理に成功しました。")

    except Exception as e:
        print(f"スクリプト実行中に予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
