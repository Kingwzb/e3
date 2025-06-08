#!/usr/bin/env python3
"""
Script to update the RAG vector database with documentation files.

This script scans the data/docs directory for markdown files and updates
the FAISS vector database used by the RAG system.
"""

import os
import sys
import argparse
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import json

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.tools.vector_store import VectorStore
from app.utils.logging import logger


class DocumentProcessor:
    """Process markdown documents for vector database ingestion."""
    
    def __init__(self, docs_dir: str = "data/docs"):
        self.docs_dir = Path(docs_dir)
        self.vector_store = VectorStore()
        self.metadata_file = self.docs_dir / ".document_metadata.json"
        
    def load_existing_metadata(self) -> Dict[str, str]:
        """Load existing document metadata (file hashes)."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata file: {e}")
        return {}
    
    def save_metadata(self, metadata: Dict[str, str]):
        """Save document metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save metadata file: {e}")
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Could not calculate hash for {file_path}: {e}")
            return ""
    
    def extract_document_sections(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Extract sections from markdown content for better chunking."""
        sections = []
        current_section = {"title": "", "content": "", "level": 0}
        
        lines = content.split('\n')
        for line in lines:
            # Check if line is a header
            if line.strip().startswith('#'):
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append({
                        "content": current_section["content"].strip(),
                        "metadata": {
                            "source": str(file_path),
                            "title": current_section["title"],
                            "section_level": current_section["level"],
                            "document_type": "productivity_insights_docs"
                        }
                    })
                
                # Start new section
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                current_section = {
                    "title": title,
                    "content": line + '\n',
                    "level": level
                }
            else:
                current_section["content"] += line + '\n'
        
        # Add the last section
        if current_section["content"].strip():
            sections.append({
                "content": current_section["content"].strip(),
                "metadata": {
                    "source": str(file_path),
                    "title": current_section["title"],
                    "section_level": current_section["level"],
                    "document_type": "productivity_insights_docs"
                }
            })
        
        return sections
    
    def process_markdown_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a single markdown file into document sections."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract sections for better semantic chunking
            sections = self.extract_document_sections(content, file_path)
            
            logger.info(f"Processed {file_path.name}: {len(sections)} sections")
            return sections
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in the docs directory."""
        if not self.docs_dir.exists():
            logger.error(f"Documentation directory {self.docs_dir} does not exist")
            return []
        
        markdown_files = []
        for file_path in self.docs_dir.rglob("*.md"):
            if file_path.is_file():
                markdown_files.append(file_path)
        
        logger.info(f"Found {len(markdown_files)} markdown files")
        return markdown_files
    
    def update_vector_database(self, force_rebuild: bool = False):
        """Update the vector database with documentation files."""
        logger.info("Starting vector database update...")
        
        # Find all markdown files
        markdown_files = self.find_markdown_files()
        if not markdown_files:
            logger.warning("No markdown files found to process")
            return
        
        # Load existing metadata
        existing_metadata = self.load_existing_metadata()
        new_metadata = {}
        
        # Collect all documents to add
        all_documents = []
        files_to_process = []
        
        for file_path in markdown_files:
            file_hash = self.calculate_file_hash(file_path)
            file_key = str(file_path.relative_to(self.docs_dir))
            
            # Check if file has changed or force rebuild
            if force_rebuild or existing_metadata.get(file_key) != file_hash:
                files_to_process.append(file_path)
                logger.info(f"Processing {file_key} (changed or new)")
            else:
                logger.debug(f"Skipping {file_key} (unchanged)")
            
            new_metadata[file_key] = file_hash
        
        if not files_to_process and not force_rebuild:
            logger.info("No files to process - all documents are up to date")
            return
        
        # Process files that need updating
        for file_path in files_to_process:
            sections = self.process_markdown_file(file_path)
            all_documents.extend(sections)
        
        if all_documents:
            if force_rebuild:
                logger.info("Rebuilding vector database from scratch...")
                # Clear existing documents and rebuild
                self.vector_store.clear_documents()
                
                # Process all files for rebuild
                all_documents = []
                for file_path in markdown_files:
                    sections = self.process_markdown_file(file_path)
                    all_documents.extend(sections)
            
            # Add documents to vector store
            logger.info(f"Adding {len(all_documents)} document sections to vector database...")
            self.vector_store.add_documents(all_documents)
            
            # Save updated metadata
            self.save_metadata(new_metadata)
            
            logger.info("Vector database update completed successfully")
        else:
            logger.info("No new documents to add")
    
    def get_database_stats(self):
        """Get statistics about the current vector database."""
        try:
            stats = self.vector_store.get_stats()
            logger.info(f"Vector database statistics:")
            logger.info(f"  - Total documents: {stats.get('total_documents', 'Unknown')}")
            logger.info(f"  - Index size: {stats.get('index_size', 'Unknown')}")
            logger.info(f"  - Embedding dimension: {stats.get('embedding_dimension', 'Unknown')}")
            return stats
        except Exception as e:
            logger.error(f"Could not get database statistics: {e}")
            return {}


def main():
    """Main function to handle command line arguments and run the update."""
    parser = argparse.ArgumentParser(
        description="Update RAG vector database with documentation files"
    )
    parser.add_argument(
        "--docs-dir",
        default="data/docs",
        help="Directory containing markdown documentation files"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild of the entire vector database"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show vector database statistics"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        import logging
        logging.getLogger("ai_chat_agent").setLevel(logging.DEBUG)
    
    # Initialize processor
    processor = DocumentProcessor(args.docs_dir)
    
    try:
        if args.stats:
            processor.get_database_stats()
        else:
            processor.update_vector_database(force_rebuild=args.rebuild)
            processor.get_database_stats()
            
    except KeyboardInterrupt:
        logger.info("Update interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Update failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 