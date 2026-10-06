import re
import requests

# Each source with its category name (order here = order in TiviMate)
SOURCES = [
    ("Malayalam", "https://iptv-org.github.io/iptv/languages/mal.m3u"),
    ("Tamil",     "https://iptv-org.github.io/iptv/languages/tam.m3u"),
    ("Romaxa55",  "https://romaxa55.github.io/world_ip_tv/output/index.m3u"),
]

OUTPUT_FILE = "merged_playlist.m3u"

def set_group_title(extinf_line, category):
    """Replace or insert group-title in an #EXTINF line."""
    if 'group-title="' in extinf_line:
        # Replace existing group-title value
        return re.sub(r'group-title="[^"]*"', f'group-title="{category}"', extinf_line)
    else:
        # Insert group-title before the comma that precedes the channel name
        return re.sub(r'(#EXTINF:[^,]*),', rf'\1 group-title="{category}",', extinf_line)

def merge_playlists():
    all_lines = ["#EXTM3U"]
    seen_urls = set()

    for category, url in SOURCES:
        print(f"Downloading {url}...")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            for line in response.text.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#EXTM3U"):
                    continue
                if stripped.startswith("#EXTINF"):
                    all_lines.append(set_group_title(stripped, category))
                elif stripped.startswith("http"):
                    if stripped in seen_urls:
                        continue
                    seen_urls.add(stripped)
                    all_lines.append(stripped)
                else:
                    all_lines.append(line)
        except Exception as e:
            print(f"Failed to download {url}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines))
    print(f"Merged playlist saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_playlists()
