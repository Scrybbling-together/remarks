#!/usr/bin/env python3

import os
import glob
import time
import sqlite3
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import subprocess
from datetime import datetime
import atexit

class ProcessingLogger:
    def __init__(self, db_path="processing_log.db"):
        self.current_run_id = None
        self.conn = None
        self.db_path = db_path
        self.setup_database()
        atexit.register(self.close)

    def setup_database(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS processing_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                total_files INTEGER,
                successful_files INTEGER,
                failed_files INTEGER,
                total_duration REAL
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS file_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                file_path TEXT,
                status TEXT,
                stdout TEXT,
                stderr TEXT,
                error_message TEXT,
                processing_time REAL,
                timestamp TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES processing_runs(id)
            )
        """)
        self.conn.commit()

    def start_run(self, total_files):
        cursor = self.conn.execute(
            "INSERT INTO processing_runs (start_time, total_files) VALUES (?, ?)",
            (datetime.now(), total_files)
        )
        self.current_run_id = cursor.lastrowid
        self.conn.commit()
        return self.current_run_id

    def log_file(self, file_path, status, stdout, stderr, error_message, processing_time):
        self.conn.execute("""
            INSERT INTO file_logs 
            (run_id, file_path, status, stdout, stderr, error_message, processing_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (self.current_run_id, file_path, status, stdout, stderr, error_message, 
              processing_time, datetime.now()))
        self.conn.commit()

    def end_run(self, successful, failed, duration):
        self.conn.execute("""
            UPDATE processing_runs 
            SET end_time = ?, successful_files = ?, failed_files = ?, 
                total_duration = ?
            WHERE id = ?
        """, (datetime.now(), successful, failed, duration, self.current_run_id))
        self.conn.commit()

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()

def process_file(file_path):
    """Process a single file using remarks command"""
    start_time = time.time()

    try:
        result = subprocess.run(
            ['python', '-m', 'remarks', file_path, "tests/out/data-out"],
            capture_output=True, 
            check=True, 
            text=True,
            timeout=180,
            env={
                **os.environ,
                # remarks depends on rmc, rmc depends on inkscape, inkscape can crash in parallel
                # https://gitlab.com/inkscape/inkscape/-/issues/4716#note_1898150983
                "SELF_CALL": "anything"
            }
        )
        duration = time.time() - start_time
        return "success", file_path, result.stdout, result.stderr, None, duration
    except subprocess.TimeoutExpired as e:
        duration = time.time() - start_time
        return "timeout", file_path, e.stdout, e.stderr, str(e), duration
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        return "failed", file_path, e.stdout, e.stderr, str(e), duration

def main():
    # Create output directory
    os.makedirs("test/out/data-out", exist_ok=True)
    
    # Initialize logger
    logger = ProcessingLogger()
    
    # Find all .rm files
    files = glob.glob("tests/data-tests/*.rmn")
    total_files = len(files)
    print(f"Found {total_files} files to process")
    
    # Start run in logger
    logger.start_run(total_files)
    
    # Track timing
    start_time = time.time()
    
    # Process files in parallel with progress bar
    successful = 0
    failed = 0
    
    # Use number of CPU cores for parallel processing
    max_workers = os.cpu_count()
    
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {executor.submit(process_file, file): file 
                             for file in files}
            
                # Process as they complete with progress bar
            with tqdm(total=total_files, desc="Processing files") as pbar:
                for future in as_completed(future_to_file):
                    status, file_path, stdout, stderr, error, duration = future.result()
                    
                    # Log the result
                    logger.log_file(
                        file_path,
                        status,
                        stdout,
                        stderr,
                        error,
                        duration
                    )
                    
                    # If there's any stderr output, print it even for successful runs
                    if status != "success":
                        tqdm.write(f"\nError processing {file_path}:")
                        tqdm.write(f"Error: {error}")
                    elif stderr:
                        tqdm.write(f"\nWarning in {file_path}:")
                        tqdm.write(stderr)

                    if status == "success":
                        successful += 1
                    else:
                        failed += 1

                    pbar.update(1)
    except KeyboardInterrupt:
        print("Bye! :)")
    
    # Record final statistics
    end_time = time.time()
    total_duration = end_time - start_time
    logger.end_run(successful, failed, total_duration)
    
    # Print summary
    print("\nProcessing complete!")
    print(f"Total time: {total_duration:.2f} seconds")
    print(f"Files processed: {successful}")
    print(f"Files failed: {failed}")
    print(f"Results logged to {logger.db_path}")

if __name__ == "__main__":
    main()
