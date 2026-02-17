"""
Compile CSV chapter files from the novel folder into a single EPUB document.
All chapters are included in numeric order with proper indexing.
"""

import os
import csv
import re
from ebooklib import epub
from pathlib import Path

NOVEL_FOLDER = "novel"
EPUB_FILENAME = "The Black Technology Chat Group of the Ten Thousand Realms.epub"

def get_chapter_number(filename):
    """Extract chapter number from filename for sorting."""
    match = re.search(r'chapter_(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0

def load_chapters():
    """Load ALL chapter CSV files in numeric order."""
    chapters = []
    
    # Get all CSV files in the novel folder
    csv_files = [f for f in os.listdir(NOVEL_FOLDER) if f.startswith('chapter_') and f.endswith('.csv')]
    
    if not csv_files:
        print(f"No CSV files found in {NOVEL_FOLDER}/")
        return chapters
    
    # Sort by chapter number numerically
    csv_files.sort(key=get_chapter_number)
    
    total_files = len(csv_files)
    print(f"Found {total_files} CSV chapter files")
    
    for idx, filename in enumerate(csv_files, 1):
        filepath = os.path.join(NOVEL_FOLDER, filename)
        chapter_num = get_chapter_number(filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # Read the first (and should be only) row
                for row in reader:
                    title = row.get('Title', f'Chapter {chapter_num}').strip()
                    edited_by = row.get('Edited By', 'Unknown').strip()
                    body = row.get('Chapter Body', '').strip()
                    
                    chapters.append({
                        'number': chapter_num,
                        'title': title,
                        'edited_by': edited_by,
                        'body': body,
                        'file': filename
                    })
                    break  # Only process first row
                    
        except Exception as e:
            # Add chapter with error placeholder
            print(f"  Error reading {filename}: {str(e)[:50]}")
            chapters.append({
                'number': chapter_num,
                'title': f'Chapter {chapter_num} [ERROR]',
                'edited_by': 'Unknown',
                'body': f'Failed to load chapter: {str(e)[:100]}',
                'file': filename
            })
    
    print(f"Loaded {len(chapters)} chapters (all files included)")
    return chapters

def create_epub(chapters):
    """Create EPUB from all chapters with proper indexing."""
    if not chapters:
        print("No chapters to create EPUB")
        return False
    
    # Create EPUB book
    book = epub.EpubBook()
    book.set_identifier(f'btc_novel_{len(chapters)}_chapters')
    book.set_title('The Black Technology Chat Group of the Ten Thousand Realms')
    book.set_language('en')
    book.add_author('Unknown')
    
    print(f"\nCreating EPUB with {len(chapters)} chapters...")
    
    epub_chapters = []
    
    for idx, chapter in enumerate(chapters, 1):
        try:
            # Create chapter HTML
            c = epub.EpubHtml()
            c.file_name = f'chapter_{idx:04d}.xhtml'
            
            # Create indexed title: "Chapter N: Title"
            indexed_title = f"Chapter {chapter['number']}: {chapter['title']}"
            c.title = indexed_title
            
            # Build HTML content
            content = f"<h1>{indexed_title}</h1>\n"
            
            if chapter['edited_by'] and chapter['edited_by'] != 'Unknown':
                content += f"<p><em>Edited by: {chapter['edited_by']}</em></p>\n"
            
            # Add all body paragraphs
            if chapter['body']:
                body_paragraphs = chapter['body'].split('\n')
                for para in body_paragraphs:
                    para = para.strip()
                    if para:
                        content += f"<p>{para}</p>\n"
            
            c.content = content
            book.add_item(c)
            epub_chapters.append(c)
            
            if idx % 50 == 0:
                print(f"  Processed {idx}/{len(chapters)} chapters...")
            
        except Exception as e:
            print(f"  [ERROR] Failed to add chapter {idx}: {str(e)[:50]}")
            # Continue anyway - don't skip chapters
    
    print(f"\nAdded {len(epub_chapters)} chapters to EPUB")
    
    # Set table of contents with all chapters indexed
    book.toc = epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Add CSS styling
    style = '''
    @namespace url("http://www.w3.org/1999/xhtml");
    
    body {
        font-family: Georgia, serif;
        line-height: 1.6;
        margin: 1em;
        text-align: justify;
    }
    
    h1 {
        text-align: center;
        margin-bottom: 0.5em;
        font-size: 1.8em;
        page-break-before: always;
    }
    
    h1:first-child {
        page-break-before: avoid;
    }
    
    p {
        text-indent: 1.5em;
        margin-bottom: 0.5em;
    }
    
    p:first-of-type {
        text-indent: 0;
    }
    
    p em {
        font-style: italic;
    }
    '''
    
    nav_css = epub.EpubItem()
    nav_css.file_name = 'style/nav.css'
    nav_css.media_type = 'text/css'
    nav_css.content = style
    book.add_item(nav_css)
    
    book.spine = ['nav'] + epub_chapters
    
    # Save EPUB
    output_path = os.path.join(NOVEL_FOLDER, EPUB_FILENAME)
    try:
        epub.write_epub(output_path, book, {})
        print(f"\n[SUCCESS] EPUB created: {output_path}")
        print(f"Total chapters in EPUB: {len(epub_chapters)}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save EPUB: {str(e)}")
        return False

def main():
    """Main function."""
    print(f"=== CSV to EPUB Converter ===\n")
    
    if not os.path.exists(NOVEL_FOLDER):
        print(f"Novel folder '{NOVEL_FOLDER}' not found!")
        return
    
    chapters = load_chapters()
    
    if chapters:
        create_epub(chapters)
    else:
        print("No chapters found to process")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")

def create_epub(chapters):
    """Create EPUB from chapters."""
    if not chapters:
        print("No chapters to create EPUB")
        return False
    
    # Create EPUB book
    book = epub.EpubBook()
    book.set_identifier(f'btc_novel_{len(chapters)}_chapters')
    book.set_title('The Black Technology Chat Group of the Ten Thousand Realms')
    book.set_language('en')
    book.add_author('Unknown')
    
    print(f"Creating EPUB with {len(chapters)} chapters...")
    
    epub_chapters = []
    
    for i, chapter in enumerate(chapters, 1):
        try:
            # Create chapter
            c = epub.EpubHtml()
            c.file_name = f'chapter_{i:04d}.xhtml'
            c.title = chapter['title']
            
            # Build content
            content = f"<h1>{chapter['title']}</h1>\n"
            
            if chapter['edited_by'] and chapter['edited_by'] != 'Unknown':
                content += f"<p><em>Edited by: {chapter['edited_by']}</em></p>\n"
            
            # Add paragraphs from body
            body_paragraphs = chapter['body'].split('\n')
            for para in body_paragraphs:
                if para.strip():
                    content += f"<p>{para.strip()}</p>\n"
            
            c.content = content
            book.add_item(c)
            epub_chapters.append(c)
            
            print(f"  Added chapter {i}: {chapter['title']}")
            
        except Exception as e:
            print(f"Error creating chapter {i}: {str(e)}")
            continue
    
    if not epub_chapters:
        print("No chapters were added to EPUB")
        return False
    
    # Set table of contents and spine
    book.toc = epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Add CSS styling
    style = '''
    @namespace url("http://www.w3.org/1999/xhtml");
    
    body {
        font-family: Georgia, serif;
        line-height: 1.6;
        margin: 1em;
        text-align: justify;
    }
    
    h1 {
        text-align: center;
        margin-bottom: 0.5em;
        font-size: 1.8em;
        page-break-before: always;
    }
    
    h1:first-child {
        page-break-before: avoid;
    }
    
    p {
        text-indent: 1.5em;
        margin-bottom: 0.5em;
    }
    
    p:first-of-type {
        text-indent: 0;
    }
    
    p em {
        font-style: italic;
    }
    '''
    
    nav_css = epub.EpubItem()
    nav_css.file_name = 'style/nav.css'
    nav_css.media_type = 'text/css'
    nav_css.content = style
    book.add_item(nav_css)
    
    book.spine = ['nav'] + epub_chapters
    
    # Save EPUB
    output_path = os.path.join(NOVEL_FOLDER, EPUB_FILENAME)
    try:
        epub.write_epub(output_path, book, {})
        print(f"\n[SUCCESS] EPUB created: {output_path}")
        print(f"Total chapters: {len(epub_chapters)}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save EPUB: {str(e)}")
        return False

def main():
    """Main function."""
    print(f"=== CSV to EPUB Converter ===\n")
    
    if not os.path.exists(NOVEL_FOLDER):
        print(f"Novel folder '{NOVEL_FOLDER}' not found!")
        return
    
    chapters = load_chapters()
    
    if chapters:
        create_epub(chapters)
    else:
        print("No chapters found to process")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
