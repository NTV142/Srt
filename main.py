import datetime
import re
import os
from ytmusicapi import YTMusic

def extract_video_id(input_str):
    input_str = input_str.strip()
    regex = r'(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/watch\?v=|\/watch\?.+&v=)([^#\&\?]{11})'
    match = re.search(regex, input_str)
    return match.group(1) if match else (input_str if len(input_str) == 11 else None)

def format_time(ms):
    if ms is None or ms < 0: ms = 0
    td = datetime.timedelta(milliseconds=ms)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = int(ms % 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def main():
    # GitHubの環境変数、または手動テスト用のテキストからURL/IDを取得
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
        watch_playlist = yt.get_watch_playlist(videoId=video_id)
        lyrics_browse_id = watch_playlist.get("lyrics")
        if not lyrics_browse_id:
            print("エラー: 歌詞データが存在しません。")
            return
            
        lyrics_data = yt.get_lyrics(browseId=lyrics_browse_id, timestamps=True)
        
        srt_content = ""
        for i, line in enumerate(lyrics_data.lyrics):
            start_ms = line.start_time
            end_ms = line.end_time or (start_ms + 3000)
            srt_content += f"{i + 1}\n{format_time(start_ms)} --> {format_time(end_ms)}\n{line.text}\n\n"
        
        # 成果物として成果を保存
        with open("lyrics.srt", "w", encoding="utf-8") as f:
            f.write(srt_content)
        
        # GitHub Pagesで見えるようにHTMLを書き換える
        html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>YTM Lyrics Result</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f5f5f5; }}
        .box {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        textarea {{ width: 100%; height: 400px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="box">
        <h2>取得完了 (ID: {video_id})</h2>
        <p>以下のSRTテキストをコピーして使用してください。</p>
        <textarea readonly>{srt_content}</textarea>
    </div>
</body>
</html>"""
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_template)
            
        print("インデックスHTMLとSRTの生成に成功しました。")

    except Exception as e:
        print(f"実行エラー: {e}")

if __name__ == "__main__":
    main()

