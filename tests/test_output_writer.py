"""Unit tests for Output Writer."""

import unittest
import os
import json
import sqlite3
import csv
from tempfile import NamedTemporaryFile
from scraper.output_writer import OutputWriter


class TestOutputWriter(unittest.TestCase):
    """Test cases for OutputWriter."""
    
    def test_csv_writer_writes_url(self):
        """Test that CSV writer writes URLs correctly."""
        with NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_file = f.name
        
        try:
            writer = OutputWriter(temp_file, 'CSV')
            writer.write_url(
                url="https://example.com",
                source_url="https://seed.com",
                depth=1,
                status_code=200,
            )
            writer.close()
            
            # Read and verify
            with open(temp_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['url'], "https://example.com")
                self.assertEqual(rows[0]['source_url'], "https://seed.com")
                self.assertEqual(rows[0]['depth'], "1")
                self.assertEqual(rows[0]['status_code'], "200")
        finally:
            os.unlink(temp_file)
    
    def test_json_writer_writes_url(self):
        """Test that JSON writer writes URLs correctly."""
        with NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            writer = OutputWriter(temp_file, 'JSON')
            writer.write_url(
                url="https://example.com",
                source_url="https://seed.com",
                depth=1,
            )
            writer.close()
            
            # Read and verify
            with open(temp_file, 'r') as f:
                data = json.load(f)
                self.assertEqual(len(data), 1)
                self.assertEqual(data[0]['url'], "https://example.com")
                self.assertEqual(data[0]['source_url'], "https://seed.com")
                self.assertEqual(data[0]['depth'], 1)
        finally:
            os.unlink(temp_file)
    
    def test_sqlite_writer_writes_url(self):
        """Test that SQLite writer writes URLs correctly."""
        with NamedTemporaryFile(delete=False, suffix='.db') as f:
            temp_file = f.name
        
        try:
            writer = OutputWriter(temp_file, 'SQLite')
            writer.write_url(
                url="https://example.com",
                source_url="https://seed.com",
                depth=1,
                status_code=200,
            )
            writer.close()
            
            # Read and verify
            conn = sqlite3.connect(temp_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM links WHERE url = ?", ("https://example.com",))
            row = cursor.fetchone()
            conn.close()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "https://example.com")
            self.assertEqual(row[1], "https://seed.com")
            self.assertEqual(row[2], 1)
        finally:
            os.unlink(temp_file)
    
    def test_sqlite_writer_handles_duplicates(self):
        """Test that SQLite writer handles duplicate URLs."""
        with NamedTemporaryFile(delete=False, suffix='.db') as f:
            temp_file = f.name
        
        try:
            writer = OutputWriter(temp_file, 'SQLite')
            # Write same URL twice
            writer.write_url(
                url="https://example.com",
                source_url="https://seed.com",
                depth=1,
            )
            writer.write_url(
                url="https://example.com",
                source_url="https://other.com",
                depth=2,
            )
            writer.close()
            
            # Verify only one entry exists
            conn = sqlite3.connect(temp_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM links")
            count = cursor.fetchone()[0]
            conn.close()
            
            self.assertEqual(count, 1)
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()
