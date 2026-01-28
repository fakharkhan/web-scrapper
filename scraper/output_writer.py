"""Output Writers: Handles incremental writing to CSV/JSON/SQLite."""

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class OutputWriter:
    """Writes discovered URLs incrementally to various formats."""
    
    def __init__(self, output_file: str, output_format: str = 'CSV'):
        """
        Initialize output writer.
        
        Args:
            output_file: Path to output file
            output_format: Format type (CSV, JSON, or SQLite)
        """
        self.output_file = output_file
        self.output_format = output_format.upper()
        
        # Initialize format-specific writers
        if self.output_format == 'CSV':
            self._init_csv()
        elif self.output_format == 'JSON':
            self._init_json()
        elif self.output_format == 'SQLITE':
            self._init_sqlite()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _init_csv(self) -> None:
        """Initialize CSV writer."""
        self.file = open(self.output_file, 'w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(
            self.file,
            fieldnames=['url', 'source_url', 'depth', 'timestamp', 'status_code', 'redirect_target']
        )
        self.writer.writeheader()
    
    def _init_json(self) -> None:
        """Initialize JSON writer."""
        self.file = open(self.output_file, 'w', encoding='utf-8')
        self.entries = []
        # Write opening bracket for JSON array
        self.file.write('[\n')
        self.first_entry = True
    
    def _init_sqlite(self) -> None:
        """Initialize SQLite writer."""
        self.conn = sqlite3.connect(self.output_file)
        self.cursor = self.conn.cursor()
        
        # Create table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                url TEXT PRIMARY KEY,
                source_url TEXT,
                depth INTEGER,
                timestamp TEXT,
                status_code INTEGER,
                redirect_target TEXT
            )
        ''')
        self.conn.commit()
    
    def write_url(
        self,
        url: str,
        source_url: str,
        depth: int,
        status_code: Optional[int] = None,
        redirect_target: Optional[str] = None,
    ) -> None:
        """
        Write a discovered URL to output.
        
        Args:
            url: Discovered URL
            source_url: URL where this link was found
            depth: Depth from seed URL
            status_code: HTTP status code (optional)
            redirect_target: Final URL after redirects (optional)
        """
        timestamp = datetime.utcnow().isoformat()
        
        if self.output_format == 'CSV':
            self._write_csv(url, source_url, depth, timestamp, status_code, redirect_target)
        elif self.output_format == 'JSON':
            self._write_json(url, source_url, depth, timestamp, status_code, redirect_target)
        elif self.output_format == 'SQLITE':
            self._write_sqlite(url, source_url, depth, timestamp, status_code, redirect_target)
    
    def _write_csv(
        self,
        url: str,
        source_url: str,
        depth: int,
        timestamp: str,
        status_code: Optional[int],
        redirect_target: Optional[str],
    ) -> None:
        """Write entry to CSV."""
        self.writer.writerow({
            'url': url,
            'source_url': source_url,
            'depth': depth,
            'timestamp': timestamp,
            'status_code': status_code or '',
            'redirect_target': redirect_target or '',
        })
        self.file.flush()  # Ensure incremental writing
    
    def _write_json(
        self,
        url: str,
        source_url: str,
        depth: int,
        timestamp: str,
        status_code: Optional[int],
        redirect_target: Optional[str],
    ) -> None:
        """Write entry to JSON."""
        entry = {
            'url': url,
            'source_url': source_url,
            'depth': depth,
            'timestamp': timestamp,
        }
        
        if status_code is not None:
            entry['status_code'] = status_code
        if redirect_target:
            entry['redirect_target'] = redirect_target
        
        # Add comma before entry if not first
        if not self.first_entry:
            self.file.write(',\n')
        else:
            self.first_entry = False
        
        json.dump(entry, self.file, indent=2)
        self.file.flush()  # Ensure incremental writing
    
    def _write_sqlite(
        self,
        url: str,
        source_url: str,
        depth: int,
        timestamp: str,
        status_code: Optional[int],
        redirect_target: Optional[str],
    ) -> None:
        """Write entry to SQLite."""
        # Use INSERT OR IGNORE to handle duplicates
        self.cursor.execute('''
            INSERT OR IGNORE INTO links 
            (url, source_url, depth, timestamp, status_code, redirect_target)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (url, source_url, depth, timestamp, status_code, redirect_target))
        self.conn.commit()  # Commit after each write for incremental persistence
    
    def close(self) -> None:
        """Close output file and finalize format-specific structures."""
        if self.output_format == 'CSV':
            self.file.close()
        elif self.output_format == 'JSON':
            # Close JSON array
            self.file.write('\n]')
            self.file.close()
        elif self.output_format == 'SQLITE':
            self.conn.close()
