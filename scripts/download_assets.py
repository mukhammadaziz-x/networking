import os
import urllib.request

def download_file(url, dest_path):
    print(f"Downloading {url} to {dest_path}...")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        with open(dest_path, 'wb') as out_file:
            out_file.write(response.read())
    print("Success.")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_css_dir = os.path.join(base_dir, "app", "static", "css")
    
    static_js_dir = os.path.join(base_dir, "app", "static", "js")
    
    # Files to download
    files = {
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css": 
            os.path.join(static_css_dir, "bootstrap.min.css"),
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js": 
            os.path.join(static_js_dir, "bootstrap.bundle.min.js"),
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css": 
            os.path.join(static_css_dir, "bootstrap-icons.css"),
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/fonts/bootstrap-icons.woff2": 
            os.path.join(static_css_dir, "fonts", "bootstrap-icons.woff2"),
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/fonts/bootstrap-icons.woff": 
            os.path.join(static_css_dir, "fonts", "bootstrap-icons.woff"),
        "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.js":
            os.path.join(static_js_dir, "chart.umd.js"),
    }
    
    for url, dest in files.items():
        try:
            download_file(url, dest)
        except Exception as e:
            print(f"Error downloading {url}: {e}")

if __name__ == "__main__":
    main()
