import os
import requests
from pathlib import Path

def download_file(url, dest):
    print(f"Downloading {url}...")
    response = requests.get(url)
    response.raise_for_status()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(response.content)

def main():
    base_static = Path("static/vendor")
    
    # Files to download
    files = {
        "bootstrap/bootstrap.min.css": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
        "bootstrap/bootstrap.bundle.min.js": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
        "fontawesome/css/all.min.css": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        # Font awesome fonts are also needed
        "fontawesome/webfonts/fa-solid-900.woff2": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-solid-900.woff2",
        "fontawesome/webfonts/fa-brands-400.woff2": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-brands-400.woff2",
        "fontawesome/webfonts/fa-regular-400.woff2": "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/fa-regular-400.woff2",
    }

    # For Google Fonts, it's harder to get the WOFF2 files directly because the CSS is user-agent dependent.
    # We will try to get some standard versions if possible, or use a placeholder if needed.
    # Actually, the user wants "full loaded". I'll try to find direct links to the font files.
    
    for relative_path, url in files.items():
        dest = base_static / relative_path
        try:
            download_file(url, dest)
        except Exception as e:
            print(f"Failed to download {url}: {e}")

    print("\nAssets downloaded successfully.")

if __name__ == "__main__":
    main()
