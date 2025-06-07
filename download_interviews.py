import os
import requests
from bs4 import BeautifulSoup
import yt_dlp
import re
from pathlib import Path
from urllib.parse import urljoin

# Create necessary directories
DATA_DIR = Path("data")
MEDIA_DIR = DATA_DIR / "media"
AUDIO_DIR = MEDIA_DIR / "audio"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
TIMESTAMPED_DIR = TRANSCRIPTS_DIR / "timestamped"
PLAIN_DIR = TRANSCRIPTS_DIR / "plain"

for dir_path in [DATA_DIR, MEDIA_DIR, AUDIO_DIR, TRANSCRIPTS_DIR, TIMESTAMPED_DIR, PLAIN_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

def clean_filename(name):
    """Clean a string to be used as a filename."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def download_file(url, save_path):
    if Path(save_path).exists():
        print(f"Already downloaded: {save_path}")
        return
    """Download a file from URL to save_path."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def download_youtube_video(url, output_path):
    if Path(output_path).exists():
        print(f"Already downloaded: {output_path}")
        return
    """Download a YouTube video using yt-dlp."""
    ydl_opts = {
        'format': 'best',
        'outtmpl': str(output_path),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"Error downloading YouTube video {url}: {e}")
        return False

def main():
    # Delete the old HTML file if it exists
    if os.path.exists('interview_library.html'):
        os.remove('interview_library.html')

    # Base URL for the website
    base_url = "https://www.kennesaw.edu"
    
    # URL of the interview library page
    url = f"{base_url}/coles/centers/accountable-leaders-center/interview-library.php"
    
    # Get the page content
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the table with interview data
    table = soup.find('table')
    if not table:
        print("Could not find the interview table on the page")
        return
    
    # Process each row in the table
    interviews = []
    for row in table.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) == 3:
            leader_name = cols[0].get_text(strip=True)
            organization = cols[1].get_text(strip=True)
            media_link = cols[0].find('a')['href'] if cols[0].find('a') else None
            transcript_link = cols[2].find('a')['href'] if cols[2].find('a') else None
            
            # Convert relative transcript URL to absolute URL
            if transcript_link and not transcript_link.startswith(('http://', 'https://')):
                transcript_link = urljoin(base_url, transcript_link)
            
            # Clean names for filenames
            clean_leader = clean_filename(leader_name)
            
            # Download media based on type
            if media_link:
                if 'youtube.com' in media_link or 'youtu.be' in media_link:
                    # It's a YouTube video
                    video_path = MEDIA_DIR / f"{clean_leader}.mp4"
                    download_youtube_video(media_link, video_path)
                    media_type = "video"
                elif media_link.endswith('.mp3'):
                    # It's an audio file
                    audio_path = AUDIO_DIR / f"{clean_leader}.mp3"
                    download_file(media_link, audio_path)
                    media_type = "audio"
                else:
                    media_type = "unknown"
            else:
                media_type = "none"
            
            # Download transcript if available
            if transcript_link:
                transcript_path = PLAIN_DIR / f"{clean_leader}.docx"
                download_file(transcript_link, transcript_path)
            
            interviews.append({
                'leader': leader_name,
                'organization': organization,
                'media_link': media_link,
                'media_type': media_type,
                'transcript_link': transcript_link,
                'local_media': f"data/media/{clean_leader}.mp4" if media_type == "video" else 
                              f"data/media/audio/{clean_leader}.mp3" if media_type == "audio" else None,
                'local_transcript': f"data/transcripts/plain/{clean_leader}.docx" if transcript_link else None,
                'timestamped_transcript': None  # To be filled if available
            })
    
    # Generate markdown table
    markdown_content = """# Accountable Leaders Interview Library

| Leader | Organization | Media Type | Media Link | Transcript | Timestamped Transcript | Local Files |
|--------|--------------|------------|------------|------------|----------------------|-------------|
"""
    
    for interview in interviews:
        markdown_content += f"| {interview['leader']} | {interview['organization']} | "
        markdown_content += f"{interview['media_type'].title()} | " if interview['media_type'] != "none" else "N/A | "
        markdown_content += f"[Link]({interview['media_link']}) | " if interview['media_link'] else "N/A | "
        markdown_content += f"[Link]({interview['transcript_link']}) | " if interview['transcript_link'] else "N/A | "
        markdown_content += f"[Link]({interview['timestamped_transcript']}) | " if interview['timestamped_transcript'] else "N/A | "
        markdown_content += f"[Media]({interview['local_media']}) [Transcript]({interview['local_transcript']}) |\n" if interview['local_media'] and interview['local_transcript'] else \
                           f"[Media]({interview['local_media']}) |\n" if interview['local_media'] else \
                           f"[Transcript]({interview['local_transcript']}) |\n" if interview['local_transcript'] else "N/A |\n"
    
    # Save markdown file
    with open('interview_library.md', 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    # Generate HTML table
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accountable Leaders Interview Library</title>
    <style>
        body { font-family: 'Montserrat', Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 1100px; margin: 40px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); padding: 32px 32px 24px 32px; }
        h1 { text-align: center; font-size: 2.2rem; font-weight: 700; margin-bottom: 32px; margin-top: 0; }
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin: 0 auto 24px auto; background: #fff; }
        thead tr { background: #FFD233; }
        th { color: #222; font-weight: 700; padding: 14px 10px; font-size: 1rem; border-bottom: 2px solid #e0e0e0; text-align: left; letter-spacing: 0.03em; }
        td { padding: 12px 10px; border-bottom: 1px solid #e0e0e0; font-size: 1rem; color: #222; }
        tr:last-child td { border-bottom: none; }
        tr:nth-child(even) td { background: #faf9f6; }
        .badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.95em; font-weight: 600; text-decoration: none; }
        .badge-local { background: #e8f5e9; color: #2e7d32; border: 1px solid #b2dfdb; }
        .badge-remote { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
        .badge-pending { background: #fffde7; color: #ef6c00; border: 1px solid #ffe082; }
        .legend { margin: 18px 0 30px 0; font-size: 1rem; }
        .legend span { margin-right: 24px; }
        .notes { margin-top: 32px; font-size: 1rem; color: #444; }
        .notes a { color: #1565c0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Life Stories</h1>
        <div class="legend">
            <span class="badge badge-local">Local Copy</span>
            <span class="badge badge-remote">Remote Only</span>
            <span class="badge badge-pending">Pending</span>
        </div>
        <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Leader</th>
                    <th>Organization</th>
                    <th>Media</th>
                    <th>Transcript</th>
                    <th>YouTube Transcript (Plain)</th>
                    <th>YouTube Transcript (Timestamped)</th>
                </tr>
            </thead>
            <tbody>\n'''
    for interview in interviews:
        html_content += f'<tr>'
        html_content += f'<td>{interview["leader"]}</td>'
        html_content += f'<td>{interview["organization"]}</td>'
        # Media
        if interview['local_media'] and Path(interview['local_media']).exists():
            html_content += f'<td><a class="badge badge-local" href="{interview["local_media"]}">Available</a></td>'
        elif interview['media_link']:
            html_content += f'<td><a class="badge badge-remote" href="{interview["media_link"]}">Remote Only</a></td>'
        else:
            html_content += f'<td><span class="badge badge-pending">Pending</span></td>'
        # Transcript
        if interview['local_transcript'] and Path(interview['local_transcript']).exists():
            html_content += f'<td><a class="badge badge-local" href="{interview["local_transcript"]}">Available</a></td>'
        elif interview['transcript_link']:
            html_content += f'<td><a class="badge badge-remote" href="{interview["transcript_link"]}">Remote Only</a></td>'
        else:
            html_content += f'<td><span class="badge badge-pending">Pending</span></td>'
        # YouTube Transcripts (not implemented)
        html_content += f'<td><span class="badge badge-pending">Pending</span></td>'
        html_content += f'<td><span class="badge badge-pending">Pending</span></td>'
        html_content += f'</tr>\n'
    html_content += '''            </tbody>
        </table>
        </div>
        <div class="notes">
            <strong>Notes:</strong>
            <ul>
                <li>All videos are in MP4 format</li>
                <li>Official transcripts are in DOCX format</li>
                <li>YouTube transcripts are in TXT format (when available)</li>
                <li>Original source: <a href="https://www.kennesaw.edu/coles/centers/accountable-leaders-center/interview-library.php">Accountable Leaders Center Interview Library</a></li>
            </ul>
        </div>
    </div>
</body>
</html>'''
    with open('interview_library.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    main() 