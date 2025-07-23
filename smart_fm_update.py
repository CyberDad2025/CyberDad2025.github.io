import os
import yaml
import datetime

POSTS_DIR = "_posts"
SYNC_LOG = "logs/sync-report.md"

def update_front_matter(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if lines[0].strip() != "---":
        return False

    front_matter = []
    content_start = 0
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            content_start = i + 1
            break
        front_matter.append(line)

    data = yaml.safe_load("".join(front_matter))
    updated = False

    if "title" not in data or not data["title"]:
        filename = os.path.basename(file_path).replace(".md", "")
        generated_title = filename.replace("-", " ").title()
        data["title"] = generated_title
        updated = True

    if updated:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("---\n")
            yaml.dump(data, f, allow_unicode=True)
            f.write("---\n")
            f.writelines(lines[content_start:])

    return updated

def main():
    updated_files = []
    for filename in os.listdir(POSTS_DIR):
        if filename.endswith(".md"):
            file_path = os.path.join(POSTS_DIR, filename)
            if update_front_matter(file_path):
                updated_files.append(filename)

    with open(SYNC_LOG, "w") as log_file:
        log_file.write(f"# Front Matter Sync Report ({datetime.datetime.now().isoformat()})\n\n")
        if updated_files:
            log_file.write("Updated the following files:\n")
            for f in updated_files:
                log_file.write(f"- {f}\n")
        else:
            log_file.write("No updates were necessary.\n")

if __name__ == "__main__":
    main()
