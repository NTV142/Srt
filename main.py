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
            print("エラー: この楽曲には歌詞データ（メニュー自体）が存在しません。")
            return
            
        print(f"歌詞データを要求中... (BrowseID: {lyrics_browse_id})")
        lyrics_data = yt.get_lyrics(browseId=lyrics_browse_id)
        
        # ログに取得したデータの型を出力して追跡できるようにする
        print(f"取得データの型: {type(lyrics_data)}")
        print(f"取得データの中身のキー一覧: {lyrics_data.keys() if isinstance(lyrics_data, dict) else 'Not a dict'}")

        srt_content = ""
        
        # パターン1: 辞書型で辞書内に 'lyrics' のリスト（タイムスタンプ付き）がある場合
        if isinstance(lyrics_data, dict) and "lyrics" in lyrics_data and isinstance(lyrics_data["lyrics"], list):
            print("同期歌詞（タイムスタンプ付きリスト）を検出しました。")
            lines = lyrics_data["lyrics"]
            for i, line in enumerate(lines):
                if isinstance(line, dict):
                    start_ms = line.get("start_time", 0)
                    end_ms = line.get("end_time") or (start_ms + 3000)
                    text = line.get("text", "")
                else:
                    start_ms = i * 3000
                    end_ms = start_ms + 3000
                    text = str(line)
                srt_content += f"{i + 1}\n{format_time(start_ms)} --> {format_time(end_ms)}\n{text}\n\n"
        
        # パターン2: 単なる1枚の長文テキスト（タイムスタンプなし歌詞）しか返ってこない場合
        elif isinstance(lyrics_data, dict) and "lyrics" in lyrics_data and isinstance(lyrics_data["lyrics"], str):
            print("通常の歌詞（プレーンテキスト）を検出しました。3秒ごとに疑似分割します。")
            plain_text = lyrics_data["lyrics"]
            lines = [line.strip() for line in plain_text.split("\n") if line.strip()]
            for i, line_text in enumerate(lines):
                start_ms = i * 3000
                end_ms = start_ms + 3000
                srt_content += f"{i + 1}\n{format_time(start_ms)} --> {format_time(end_ms)}\n{line_text}\n\n"
                
        else:
            print("未知のデータ構造です。テキスト抽出を試みます。")
            text_data = lyrics_data.get("lyrics", "") if isinstance(lyrics_data, dict) else str(lyrics_data)
            lines = [l.strip() for l in str(text_data).split("\n") if l.strip()]
            for i, line_text in enumerate(lines):
                start_ms = i * 3000
                end_ms = start_ms + 3000
                srt_content += f"{i + 1}\n{format_time(start_ms)} --> {format_time(end_ms)}\n{line_text}\n\n"

        if not srt_content.strip():
            print("エラー: SRTに変換できる歌詞テキストがありませんでした。")
            return

        with open("lyrics.srt", "w", encoding="utf-8") as f:
            f.write(srt_content)
        
        html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>YTM Lyrics Result</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f5f5f5; }}
        .box {{ max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        textarea {{ width: 100%; height: 400px; font-family: monospace; padding: 10px; margin-top: 10px; box-sizing: border-box; }}
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
        print(f"スクリプト実行中に予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
