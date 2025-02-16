"""URL tracking and optimization utilities"""
import os
import json
import logging
from datetime import datetime

class URLTracker:
    def __init__(self, tracking_file="processed_urls.json"):
        self.tracking_file = tracking_file
        self.processed_urls = self._load_processed_urls()
        
    def _load_processed_urls(self):
        """Load previously processed URLs from tracking file"""
        try:
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logging.error(f"Error loading processed URLs: {str(e)}")
            return {}
            
    def _save_processed_urls(self):
        """Save processed URLs to tracking file"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.processed_urls, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving processed URLs: {str(e)}")
            
    def is_url_processed(self, url):
        """Check if URL has been processed successfully"""
        return url in self.processed_urls
        
    def mark_url_processed(self, url, metadata=None):
        """Mark URL as processed with optional metadata"""
        self.processed_urls[url] = {
            'processed_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self._save_processed_urls()
        
    def get_url_metadata(self, url):
        """Get metadata for processed URL"""
        return self.processed_urls.get(url, {}).get('metadata', {}) 