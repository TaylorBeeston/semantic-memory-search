"""Chunk memory files into semantic segments."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Iterator


@dataclass
class Chunk:
    """A single chunk of text with metadata."""
    text: str
    source: str
    start_line: int
    end_line: int
    chunk_type: str  # 'header', 'paragraph', 'list', 'code'
    
    def __repr__(self):
        preview = self.text[:50].replace('\n', ' ') + '...' if len(self.text) > 50 else self.text
        return f"Chunk({self.chunk_type}, {self.source}:{self.start_line}-{self.end_line}, '{preview}')"


class Chunker:
    """Split memory files into semantic chunks."""
    
    def __init__(
        self,
        max_chunk_size: int = 512,
        overlap: int = 50,
        preserve_headers: bool = True
    ):
        """Initialize chunker.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            overlap: Characters of overlap between chunks
            preserve_headers: Keep markdown headers as separate chunks
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.preserve_headers = preserve_headers
        
    def chunk_file(self, filepath: Path) -> List[Chunk]:
        """Chunk a single file.
        
        Args:
            filepath: Path to the file to chunk
            
        Returns:
            List of Chunk objects
        """
        text = filepath.read_text(encoding='utf-8')
        lines = text.split('\n')
        
        chunks = []
        current_section = []
        current_start = 0
        in_code_block = False
        
        for i, line in enumerate(lines):
            # Track code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                
            # Header detection (markdown headers)
            if not in_code_block and re.match(r'^#{1,6}\s', line):
                # Save previous section
                if current_section:
                    section_text = '\n'.join(current_section)
                    chunks.extend(self._chunk_text(
                        section_text, 
                        str(filepath), 
                        current_start, 
                        i - 1
                    ))
                    current_section = []
                    
                # If preserving headers, make it its own chunk
                if self.preserve_headers:
                    chunks.append(Chunk(
                        text=line.strip(),
                        source=str(filepath),
                        start_line=i + 1,
                        end_line=i + 1,
                        chunk_type='header'
                    ))
                    current_start = i + 1
                else:
                    current_section.append(line)
                    current_start = i
                    
            else:
                current_section.append(line)
        
        # Don't forget the last section
        if current_section:
            section_text = '\n'.join(current_section)
            chunks.extend(self._chunk_text(
                section_text,
                str(filepath),
                current_start,
                len(lines)
            ))
            
        return chunks
    
    def _chunk_text(
        self, 
        text: str, 
        source: str, 
        start_line: int, 
        end_line: int
    ) -> List[Chunk]:
        """Split text into overlapping chunks."""
        if len(text) <= self.max_chunk_size:
            chunk_type = 'code' if text.strip().startswith('```') else 'paragraph'
            return [Chunk(
                text=text.strip(),
                source=source,
                start_line=start_line,
                end_line=end_line,
                chunk_type=chunk_type
            )]
        
        chunks = []
        pos = 0
        chunk_num = 0
        
        while pos < len(text):
            # Find chunk boundary
            chunk_end = pos + self.max_chunk_size
            
            # Try to break at a sentence or paragraph
            if chunk_end < len(text):
                # Look for sentence boundary
                for delimiter in ['.\n', '. ', '\n\n', '\n']:
                    idx = text.rfind(delimiter, pos, chunk_end)
                    if idx != -1:
                        chunk_end = idx + len(delimiter)
                        break
            
            chunk_text = text[pos:chunk_end].strip()
            if chunk_text:
                # Estimate line numbers
                lines_before = text[:pos].count('\n')
                chunk_lines = chunk_text.count('\n')
                
                chunks.append(Chunk(
                    text=chunk_text,
                    source=source,
                    start_line=start_line + lines_before,
                    end_line=start_line + lines_before + chunk_lines,
                    chunk_type='paragraph'
                ))
            
            # Move position with overlap
            pos = chunk_end - self.overlap
            chunk_num += 1
            
            # Safety break
            if chunk_num > 100:
                break
                
        return chunks
    
    def chunk_directory(self, directory: Path, pattern: str = "*.md") -> Iterator[Chunk]:
        """Chunk all matching files in a directory.
        
        Args:
            directory: Directory to scan
            pattern: Glob pattern for files
            
        Yields:
            Chunk objects
        """
        for filepath in directory.rglob(pattern):
            if filepath.is_file():
                try:
                    chunks = self.chunk_file(filepath)
                    for chunk in chunks:
                        yield chunk
                except Exception as e:
                    print(f"Error chunking {filepath}: {e}")
