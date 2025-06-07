# Accountable Leaders Interview Library Downloader

This project downloads and organizes interview content from the Kennesaw State University Accountable Leaders Center.

## Setup

1. Install Python 3.8 or higher
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the download script:
```bash
python download_interviews.py
```

The script will:
1. Create necessary directories:
   - `data/media/` - For video/audio files
   - `data/transcripts/plain/` - For plain transcripts
   - `data/transcripts/timestamped/` - For timestamped transcripts (if available)

2. Download all available content:
   - YouTube videos
   - Transcript files
   - Generate a markdown table with links to all content

3. Create `interview_library.md` with a table of all interviews and their content

## Directory Structure

```
.
├── README.md
├── requirements.txt
├── download_interviews.py
├── interview_library.md
└── data/
    ├── media/
    ├── transcripts/
    │   ├── plain/
    │   └── timestamped/
```

## Notes

- Videos are downloaded in the best available quality
- Transcripts are preserved in their original format (typically .docx)
- The script handles YouTube links and direct file downloads
- All files are organized by leader name 