python smart_fm_update.py
import os
import yaml

POSTS_DIR = "_posts"
DEFAULT_IMAGE = "/assets/images/post-thumbnail.jpg"

def determine_category(title):
    title = title.lower()
    if any(k in title for k in ["daily", "alert", "malware", "phishing", "threat", "scam"]):
        return "CTI"
    elif any(k in title for k in ["setup", "password", "router", "camera", "security", "authentication"]):
        return "Guide"
    elif any(k in title for k in ["tips", "privacy", "checklist", "safe", "pro tips"]):
        return "Tips"
    elif any(k in title for k in ["kids", "parent", "family", "grandparent"]):
        return "Family"
    else:
        return "General"

def has_valid_front_matter(lines):
    return lines and lines[0].strip() == "---" and "---" in lines[1:]

for filename in os.listdir(POSTS_DIR):
    if not filename.endswith(".md"):
        continue

    path = os.path.join(POSTS_DIR, filename)

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not has_valid_front_matter(lines):
        print(f"Skipped (no valid front matter): {filename}")
        continue

    end_index = lines[1:].index("---\n") + 1
    front_matter = yaml.safe_load("".join(lines[1:end_index]))
    title = front_matter.get("title", filename)

    updated = False

    if "image" not in front_matter:
        front_matter["image"] = DEFAULT_IMAGE
        updated = True

    if "category" not in front_matter:
        front_matter["category"] = determine_category(title)
        updated = True

    if updated:
        new_front = yaml.dump(front_matter, sort_keys=False)
        new_content = ["---\n"] + new_front.splitlines(keepends=True) + ["---\n"] + lines[end_index+1:]
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_content)
        print(f"✅ Updated: {filename}")
    else:
        print(f"✔️ Already good: {filename}")
