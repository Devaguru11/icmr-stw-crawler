import os
import re
import json
from datetime import datetime
from urllib.parse import urlparse, unquote

def sanitize_filename(url):
    """
    Generates a safe filename from a URL.
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = os.path.basename(path)
    
    # Remove invalid characters
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    
    # Ensure it ends with .pdf
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
        
    # Fallback if filename is empty
    if not filename or filename == '.pdf':
        filename = f"document_{hash(url)}.pdf"
        
    return filename

def generate_metadata(url, local_path, output_dir):
    """
    Generates a metadata JSON file for the downloaded PDF.
    """
    metadata = {
        "source_authority": "ICMR",
        "document_type": "Standard Treatment Workflow",
        "original_url": url,
        "local_file_path": local_path,
        "download_timestamp": datetime.now().isoformat()
    }
    
    filename = os.path.basename(local_path)
    json_filename = f"{os.path.splitext(filename)[0]}.json"
    json_path = os.path.join(output_dir, json_filename)
    
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    return json_path
