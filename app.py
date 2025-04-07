from flask import Flask, request, send_file, jsonify, render_template
from yt_dlp import YoutubeDL
import os
import uuid

app = Flask(__name__)

# Path to cookies file (optional)
COOKIES_FILE = "cookies.txt" if os.path.exists("cookies.txt") else None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'cookiefile': COOKIES_FILE,
            'skip_download': True,
            'forcejson': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = []
        for f in info.get("formats", []):
            if f.get("ext") == "mp4" and f.get("height") and 144 <= f.get("height", 0) <= 1080:
                formats.append({
                    "format_id": f["format_id"],
                    "ext": f["ext"],
                    "resolution": f.get("height", "N/A")
                })

        return jsonify({
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "formats": formats
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    format_id = data.get('format_id')

    if not url or not format_id:
        return jsonify({'error': 'Missing URL or format ID'}), 400

    try:
        temp_file = f"{uuid.uuid4()}.mp4"

        ydl_opts = {
            'quiet': True,
            'cookiefile': COOKIES_FILE,
            'format': format_id,
            'outtmpl': temp_file
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return_data = send_file(temp_file, as_attachment=True)

        @return_data.call_on_close
        def cleanup():
            os.remove(temp_file)

        return return_data

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)