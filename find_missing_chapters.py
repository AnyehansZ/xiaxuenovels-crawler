import os
import re

NOVEL_FOLDER = "novel"

# Get all CSV files
csv_files = [f for f in os.listdir(NOVEL_FOLDER) if f.endswith('.csv')]

# Extract chapter numbers
chapter_numbers = []
for filename in csv_files:
    match = re.search(r'chapter_(\d+)', filename)
    if match:
        chapter_numbers.append(int(match.group(1)))

chapter_numbers = sorted(chapter_numbers)
total = len(chapter_numbers)

print(f"Total chapters found: {total}\n")

# Find missing chapters
missing_chapters = []
for i in range(1, 547):
    if i not in chapter_numbers:
        missing_chapters.append(i)

if missing_chapters:
    print(f"MISSING CHAPTERS ({len(missing_chapters)}):\n")
    print(missing_chapters)
    print(f"\nMissing chapter ranges:")
    
    # Group consecutive missing chapters
    start = missing_chapters[0]
    end = missing_chapters[0]
    
    for i in range(1, len(missing_chapters)):
        if missing_chapters[i] == end + 1:
            end = missing_chapters[i]
        else:
            if start == end:
                print(f"  Chapter {start}")
            else:
                print(f"  Chapters {start}-{end}")
            start = missing_chapters[i]
            end = missing_chapters[i]
    
    # Print last group
    if start == end:
        print(f"  Chapter {start}")
    else:
        print(f"  Chapters {start}-{end}")
else:
    print("All 546 chapters present!")
