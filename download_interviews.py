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
    for row in table.find_all('tr')[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) >= 3:
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

if __name__ == "__main__":
    main() 