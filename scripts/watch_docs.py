#!/usr/bin/env python3
"""
Watch documentation files for changes and automatically update the vector database.

This script monitors the data/docs directory for file changes and automatically
updates the RAG vector database when markdown files are modified.
"""

import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.logging import logger


class DocumentChangeHandler(FileSystemEventHandler):
    """Handle file system events for documentation changes."""
    
    def __init__(self, docs_dir: Path, debounce_seconds: int = 2):
        self.docs_dir = docs_dir
        self.debounce_seconds = debounce_seconds
        self.last_update = 0
        
    def should_process_event(self, event):
        """Check if the event should trigger a vector database update."""
        if event.is_directory:
            return False
        
        # Only process markdown files
        if not event.src_path.endswith('.md'):
            return False
        
        # Debounce rapid file changes
        current_time = time.time()
        if current_time - self.last_update < self.debounce_seconds:
            return False
        
        return True
    
    def update_vector_database(self):
        """Run the vector database update script."""
        try:
            logger.info("Documentation files changed, updating vector database...")
            
            # Run the update script
            result = subprocess.run([
                sys.executable, 
                str(project_root / "scripts" / "update_vector_db.py"),
                "--docs-dir", str(self.docs_dir)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Vector database updated successfully")
                if result.stdout:
                    logger.debug(f"Update output: {result.stdout}")
            else:
                logger.error(f"Vector database update failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error updating vector database: {e}")
        
        self.last_update = time.time()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if self.should_process_event(event):
            logger.info(f"Detected change in {event.src_path}")
            self.update_vector_database()
    
    def on_created(self, event):
        """Handle file creation events."""
        if self.should_process_event(event):
            logger.info(f"Detected new file {event.src_path}")
            self.update_vector_database()
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if self.should_process_event(event):
            logger.info(f"Detected deletion of {event.src_path}")
            # For deletions, we need to rebuild the entire database
            try:
                logger.info("File deleted, rebuilding vector database...")
                result = subprocess.run([
                    sys.executable, 
                    str(project_root / "scripts" / "update_vector_db.py"),
                    "--docs-dir", str(self.docs_dir),
                    "--rebuild"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("Vector database rebuilt successfully")
                else:
                    logger.error(f"Vector database rebuild failed: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error rebuilding vector database: {e}")
            
            self.last_update = time.time()


def main():
    """Main function to start the file watcher."""
    docs_dir = project_root / "data" / "docs"
    
    if not docs_dir.exists():
        logger.error(f"Documentation directory {docs_dir} does not exist")
        sys.exit(1)
    
    logger.info(f"Starting documentation file watcher for {docs_dir}")
    logger.info("Press Ctrl+C to stop watching")
    
    # Create event handler and observer
    event_handler = DocumentChangeHandler(docs_dir)
    observer = Observer()
    observer.schedule(event_handler, str(docs_dir), recursive=True)
    
    try:
        # Start watching
        observer.start()
        logger.info("File watcher started successfully")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
        observer.stop()
    except Exception as e:
        logger.error(f"File watcher error: {e}")
        observer.stop()
        sys.exit(1)
    
    observer.join()
    logger.info("File watcher stopped")


if __name__ == "__main__":
    main() 