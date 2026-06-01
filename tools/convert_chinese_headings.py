#!/usr/bin/env python3
"""Convert Chinese numeral chapter headings to Arabic numerals in specs/refs/ and specs/evals/."""

import os
import re
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECS_DIR = os.path.join(PROJECT_DIR, "specs")

CN_TO_ARABIC = {
    "一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
    "六": "6", "七": "7", "八": "8", "九": "9", "十": "10",
    "十一": "11", "十二": "12", "十三": "13", "十四": "14", "十五": "15",
    "十六": "16", "十七": "17", "十八": "18", "十九": "19", "二十": "20",
}

HEADING_PATTERN = re.compile(r'^(#{1,6})\s+([一二三四五六七八九十]+)、(.+)$', re.MULTILINE)

EVAL_NUMBER_ATTRIBUTION = "> 编号归属：70-89 内部调研\n"


def convert_headings(content):
    def replace_heading(match):
        hashes = match.group(1)
        cn_num = match.group(2)
        title = match.group(3)
        arabic = CN_TO_ARABIC.get(cn_num, cn_num)
        return f"{hashes} {arabic}. {title}"

    return HEADING_PATTERN.sub(replace_heading, content)


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    content = convert_headings(original)

    if "specs/evals/" in filepath.replace("\\", "/"):
        if EVAL_NUMBER_ATTRIBUTION in content:
            content = content.replace(EVAL_NUMBER_ATTRIBUTION, "")
            print(f"  Removed incorrect 编号归属 from {os.path.basename(filepath)}")

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    target_dirs = [
        os.path.join(SPECS_DIR, "refs"),
        os.path.join(SPECS_DIR, "evals"),
    ]

    changed = 0
    for target_dir in target_dirs:
        if not os.path.isdir(target_dir):
            continue
        print(f"\nProcessing {target_dir}...")
        for fname in sorted(os.listdir(target_dir)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(target_dir, fname)
            if process_file(fpath):
                print(f"  Updated: {fname}")
                changed += 1

    print(f"\nTotal files changed: {changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())