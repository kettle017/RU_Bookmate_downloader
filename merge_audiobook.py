#!/usr/bin/env python3
"""
Script to merge audiobook chapters into a single file
"""

import os
import subprocess
import json
from pathlib import Path
import sys

def merge_audiobook_chapters(audiobook_path, cleanup_chapters=True):
    """
    Merge all M4A chapter files in a directory into a single audiobook
    
    Args:
        audiobook_path: Path to the audiobook directory
        cleanup_chapters: Whether to remove individual chapter files after successful merge
    """
    audiobook_dir = Path(audiobook_path)
    
    if not audiobook_dir.exists():
        print(f"Directory not found: {audiobook_dir}")
        return
    
    # Find all M4A files and sort them naturally
    chapter_files = sorted([f for f in audiobook_dir.glob("*.m4a") if "Глава_" in f.name], 
                          key=lambda x: int(x.stem.split('_')[1]))
    
    if not chapter_files:
        print(f"No chapter files found in {audiobook_dir}")
        return
    
    print(f"Found {len(chapter_files)} chapters")
    
    # Get audiobook metadata from JSON file if available
    json_file = audiobook_dir / f"{audiobook_dir.name}.json"
    metadata = {}
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            if 'audiobook' in json_data:
                book_info = json_data['audiobook']
                
                # Extract author name
                author_name = 'Unknown Author'
                if 'authors' in book_info and book_info['authors']:
                    author_name = book_info['authors'][0].get('name', 'Unknown Author')
                
                # Extract narrator name
                narrator_name = ''
                if 'narrators' in book_info and book_info['narrators']:
                    narrator_names = [n.get('name', '') for n in book_info['narrators']]
                    narrator_name = ', '.join(filter(None, narrator_names))
                
                # Extract publisher name
                publisher_name = ''
                if 'publishers' in book_info and book_info['publishers']:
                    publisher_name = book_info['publishers'][0].get('name', '')
                
                metadata = {
                    'title': book_info.get('title', audiobook_dir.name),
                    'artist': author_name,
                    'album': book_info.get('title', audiobook_dir.name),
                    'album_artist': author_name,
                    'composer': author_name,
                    'genre': 'Audiobook',
                    'media_type': '2',  # Audiobook media type
                    'comment': book_info.get('annotation', ''),
                    'publisher': publisher_name,
                    'language': book_info.get('language', 'ru'),
                }
                
                # Add narrator if available
                if narrator_name:
                    metadata['performer'] = narrator_name
                
                # Remove empty values
                metadata = {k: v for k, v in metadata.items() if v}
    
    # Create output filename
    output_file = audiobook_dir / f"{audiobook_dir.name}_complete.m4a"
    
    # Look for cover image
    cover_image = None
    for ext in ['.jpeg', '.jpg', '.png']:
        potential_cover = audiobook_dir / f"{audiobook_dir.name}{ext}"
        if potential_cover.exists():
            cover_image = potential_cover
            break
    
    # Create a temporary file list for ffmpeg
    filelist_path = audiobook_dir / "chapters_list.txt"
    
    # Create chapter metadata file
    chapters_metadata_path = audiobook_dir / "chapters_metadata.txt"
    
    try:
        # Get chapter durations first
        print("📊 Analyzing chapter durations...")
        chapter_durations = []
        current_time = 0.0
        
        for chapter_file in chapter_files:
            # Get duration of each chapter using ffprobe
            duration_cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(chapter_file)
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            
            if duration_result.returncode == 0:
                duration = float(duration_result.stdout.strip())
                chapter_durations.append((current_time, current_time + duration, chapter_file))
                current_time += duration
            else:
                print(f"⚠️ Could not get duration for {chapter_file.name}")
                chapter_durations.append((current_time, current_time + 180, chapter_file))  # Fallback: 3 minutes
                current_time += 180
        
        # Write file list for ffmpeg concat
        with open(filelist_path, 'w', encoding='utf-8') as f:
            for chapter_file in chapter_files:
                # Use absolute path and escape single quotes for ffmpeg
                abs_path = str(chapter_file.absolute()).replace("'", "'\"'\"'")
                f.write(f"file '{abs_path}'\n")
        
        # Create chapters metadata file
        with open(chapters_metadata_path, 'w', encoding='utf-8') as f:
            f.write(";FFMETADATA1\n")
            
            # Add global metadata
            if metadata:
                for key, value in metadata.items():
                    if value:
                        # Escape special characters for ffmetadata
                        escaped_value = str(value).replace('=', '\\=').replace(';', '\\;').replace('#', '\\#').replace('\\', '\\\\')
                        f.write(f"{key.upper()}={escaped_value}\n")
            
            # Add chapter markers
            for i, (start_time, end_time, chapter_file) in enumerate(chapter_durations):
                chapter_num = i + 1
                chapter_title = f"Глава {chapter_num}"
                
                f.write("\n[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")  # Milliseconds
                f.write(f"START={int(start_time * 1000)}\n")
                f.write(f"END={int(end_time * 1000)}\n")
                f.write(f"title={chapter_title}\n")
        
        print(f"Merging chapters into: {output_file}")
        
        # FFmpeg command to concatenate files
        cmd = [
            'ffmpeg', '-y',  # -y to overwrite existing files
            '-f', 'concat',
            '-safe', '0',
            '-i', str(filelist_path),
            '-i', str(chapters_metadata_path),  # Chapter metadata
        ]
        
        # Add cover image if available
        if cover_image:
            cmd.extend(['-i', str(cover_image)])
            cmd.extend(['-c:v', 'copy'])  # Copy video/image stream
            cmd.extend(['-c:a', 'copy'])  # Copy audio stream
            cmd.extend(['-disposition:v:0', 'attached_pic'])  # Mark image as cover
            cmd.extend(['-map_metadata', '1'])  # Use metadata from chapters file
        else:
            cmd.extend(['-c', 'copy'])  # Copy without re-encoding
            cmd.extend(['-map_metadata', '1'])  # Use metadata from chapters file
        
        # Add comprehensive metadata if available (this will override the metadata file if needed)
        if metadata:
            for key, value in metadata.items():
                if value:  # Only add non-empty values
                    cmd.extend(['-metadata', f'{key}={value}'])
        else:
            # Fallback metadata
            cmd.extend(['-metadata', f'title={audiobook_dir.name}'])
            cmd.extend(['-metadata', 'genre=Audiobook'])
            cmd.extend(['-metadata', 'media_type=2'])
        
        cmd.append(str(output_file))
        
        # Run ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode == 0:
            print(f"✅ Successfully merged audiobook: {output_file}")
            print(f"Original chapters: {len(chapter_files)} files")
            
            # Get file size
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"Output file size: {size_mb:.1f} MB")
            
            if cover_image:
                print(f"📷 Cover image embedded: {cover_image.name}")
            
            print(f"📑 Chapter markers added: {len(chapter_files)} chapters")
            
            # Clean up individual chapter files after successful merge (if requested)
            if cleanup_chapters:
                print("🧹 Cleaning up chapter files...")
                for chapter_file in chapter_files:
                    try:
                        chapter_file.unlink()
                        print(f"   Removed: {chapter_file.name}")
                    except OSError as e:
                        print(f"   ⚠️ Could not remove {chapter_file.name}: {e}")
                
                print(f"✨ Cleanup complete. Merged audiobook ready: {output_file.name}")
            else:
                print(f"📁 Chapter files preserved. Merged audiobook ready: {output_file.name}")
            
            return str(output_file)
        else:
            print(f"❌ Error merging audiobook:")
            print(result.stderr)
            return None
            
    finally:
        # Clean up temporary files
        if filelist_path.exists():
            filelist_path.unlink()
        if chapters_metadata_path.exists():
            chapters_metadata_path.unlink()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Merge audiobook chapters into a single file')
    parser.add_argument('audiobook_path', nargs='?', help='Path to the audiobook directory')
    parser.add_argument('--batch', action='store_true', help='Process all audiobooks in mybooks/audiobook/ directory')
    parser.add_argument('--batch-series', action='store_true', help='Process all audiobooks in mybooks/series/ directory')
    parser.add_argument('--batch-all', action='store_true', help='Process all audiobooks in both mybooks/audiobook/ and mybooks/series/ directories')
    parser.add_argument('--force', action='store_true', help='Overwrite existing merged files')
    parser.add_argument('--keep-chapters', action='store_true', help='Keep individual chapter files after merging')
    args = parser.parse_args()
    
    print("🎧 Audiobook Chapter Merger")
    print("=" * 50)
    
    def process_directory(base_dir, dir_type):
        """Process audiobooks in a directory"""
        if not base_dir.exists():
            print(f"❌ {base_dir} directory not found")
            return 0, 0
        
        audiobook_dirs = []
        
        if dir_type == "series":
            # For series, we need to go one level deeper (author -> books)
            for author_dir in base_dir.iterdir():
                if author_dir.is_dir() and not author_dir.name.startswith('.'):
                    for book_dir in author_dir.iterdir():
                        if book_dir.is_dir() and not book_dir.name.startswith('.'):
                            audiobook_dirs.append(book_dir)
        else:
            # For regular audiobooks, books are directly in the directory
            audiobook_dirs = [d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
        if not audiobook_dirs:
            print(f"❌ No audiobook directories found in {base_dir}")
            return 0, 0
        
        print(f"Found {len(audiobook_dirs)} audiobooks to process in {dir_type}")
        successful = 0
        
        for audiobook_dir in audiobook_dirs:
            output_file = audiobook_dir / f"{audiobook_dir.name.split('. ', 1)[-1] if '. ' in audiobook_dir.name else audiobook_dir.name}_complete.m4a"
            
            # Skip if already merged and not forcing
            if output_file.exists() and not args.force:
                print(f"⏭️  Skipping {audiobook_dir.name} (already merged, use --force to overwrite)")
                continue
            
            # Show the full path for series books to indicate author
            if dir_type == "series":
                author_name = audiobook_dir.parent.name
                print(f"\n📚 Processing: {author_name} - {audiobook_dir.name}")
            else:
                print(f"\n📚 Processing: {audiobook_dir.name}")
            
            merged_file = merge_audiobook_chapters(str(audiobook_dir), cleanup_chapters=not args.keep_chapters)
            if merged_file:
                successful += 1
        
        return successful, len(audiobook_dirs)
    
    if args.batch or args.batch_all:
        # Process regular audiobooks
        audiobooks_dir = Path("mybooks/audiobook")
        total_successful, total_books = process_directory(audiobooks_dir, "audiobook")
        
        if args.batch_all:
            # Also process series audiobooks
            series_dir = Path("mybooks/series")
            series_successful, series_books = process_directory(series_dir, "series")
            total_successful += series_successful
            total_books += series_books
        
        print(f"\n✅ Successfully processed {total_successful}/{total_books} audiobooks")
        
    elif args.batch_series:
        # Process only series audiobooks
        series_dir = Path("mybooks/series")
        successful, total_books = process_directory(series_dir, "series")
        print(f"\n✅ Successfully processed {successful}/{total_books} audiobooks")
        
    else:
        # Process single audiobook
        if args.audiobook_path:
            audiobook_path = args.audiobook_path
        else:
            audiobook_path = input("Enter the path to the audiobook directory: ").strip()
        
        if os.path.exists(audiobook_path):
            merged_file = merge_audiobook_chapters(audiobook_path, cleanup_chapters=not args.keep_chapters)
            if merged_file:
                print(f"\n📱 Transfer this file to your iPhone: {merged_file}")
        else:
            print(f"Audiobook directory not found: {audiobook_path}")

if __name__ == "__main__":
    main()
