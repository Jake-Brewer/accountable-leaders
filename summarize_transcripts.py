import os
import glob
from pathlib import Path

# Placeholder for LLM summarization (basic truncation for now)
def summarize_text(text, max_length=200):
    return f"Summary: {text[:max_length]}..."

# Directories
input_dir = "data/transcripts/plain_txt"
output_dir = "data/summaries"
Path(output_dir).mkdir(parents=True, exist_ok=True)

# Process each .txt transcript
for txt_file in glob.glob(f"{input_dir}/*.txt"):
    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read()
    summary = summarize_text(text)
    output_file = os.path.join(output_dir, f"{Path(txt_file).stem}_summary.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"Created summary: {output_file}")
