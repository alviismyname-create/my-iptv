import re
import requests

# (category_name, url, flatten)
SOURCES = [
    ("Malayalam", "https://iptv-org.github.io/iptv/languages/mal.m3u", True),
    ("Tamil",     "https://iptv-org.github.io/iptv/languages/tam.m3u", True),
    ("romaxa55",  "https://romaxa55.github.io/world_ip_tv/output/index.m3u", False),
]

OUTPUT_FILE = "merged_playlist.m3u"

# Order of groups after Malayalam and Tamil.
# These must match the group-title values in the source exactly.
PRIORITY_GROUPS = [
    "India",
    "International",
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
    "South Africa",
    "Singapore",
    "New Zealand",
    "United Arab Emirates",
    "Japan",
    "Philippines",
    "South Korea",
    "Guam",
]

# Groups that always stay at the very top
TOP_GROUPS = ["Malayalam", "Tamil"]

def set_group_title(extinf_line, category):
    """Replace or insert group-title in an #EXTINF line."""
    if 'group-title="' in extinf_line:
        return re.sub(r'group-title="[^"]*"', f'group-title="{category}"', extinf_line)
    else:
        return re.sub(r'(#EXTINF:[^,]*),', rf'\1 group-title="{category}",', extinf_line)

def get_group(block):
    """Extract group-title from a channel block."""
    for line in block:
        m = re.search(r'group-title="([^"]*)"', line)
        if m:
            return m.group(1)
    return ""

def merge_playlists():
    blocks = []
    seen_urls = set()

    for category, url, flatten in SOURCES:
        print(f"Downloading {url} (flatten={flatten})...")
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            current_block = []
            for line in response.text.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#EXTM3U"):
                    continue

                if stripped.startswith("#EXTINF"):
                    if current_block:
                        blocks.append(current_block)
                        current_block = []
                    if flatten:
                        current_block.append(set_group_title(stripped, category))
                    else:
                        if 'group-title="' not in stripped:
                            stripped = set_group_title(stripped, category)
                        current_block.append(stripped)

                elif stripped.startswith("#EXTGRP"):
                    if not flatten:
                        current_block.append(stripped)

                elif stripped.startswith("http"):
                    if stripped in seen_urls:
                        current_block = []
                        continue
                    seen_urls.add(stripped)
                    current_block.append(stripped)
                    blocks.append(current_block)
                    current_block = []

                else:
                    if current_block:
                        current_block.append(line)

            if current_block:
                blocks.append(current_block)

        except Exception as e:
            print(f"Failed to download {url}: {e}")

    # Bucket blocks by their group name
    groups = {}
    seen_order = []
    for block in blocks:
        g = get_group(block)
        if g not in groups:
            groups[g] = []
            seen_order.append(g)
        groups[g].append(block)

    # Build final group order
    final_order = []
    for g in TOP_GROUPS:
        if g in groups:
            final_order.append(g)
    for g in PRIORITY_GROUPS:
        if g in groups and g not in final_order:
            final_order.append(g)
    for g in seen_order:
        if g not in final_order:
            final_order.append(g)

    # Write out
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for g in final_order:
            for block in groups[g]:
                f.write("\n".join(block) + "\n")

    print(f"Merged playlist saved to {OUTPUT_FILE}")
    print(f"Total groups: {len(final_order)}")
    print(f"Group order (first 25): {final_order[:25]}")

if __name__ == "__main__":
    merge_playlists()
