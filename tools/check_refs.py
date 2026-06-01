#!/usr/bin/env python3
"""Check § cross-references in specs/ for validity."""

import os
import re
import sys

SPECS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'specs')

# Chinese numerals mapping
CN_NUM = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
          '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}

def extract_sections(filepath):
    """Extract all section numbers from a markdown file."""
    sections = set()
    with open(filepath, 'r') as f:
        for line in f:
            # Match ## N., ### N.N, #### N.N.N headings
            m = re.match(r'^(#{2,5})\s+(\d+(?:\.\d+)*)\.?\s', line)
            if m:
                sections.add(m.group(2))
    return sections

def build_section_map():
    """Build a map of filename -> set of section numbers for all main specs."""
    section_map = {}
    for fname in sorted(os.listdir(SPECS_DIR)):
        if not fname.endswith('.md'):
            continue
        # Skip refs/ and evals/ subdirs
        fpath = os.path.join(SPECS_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        sections = extract_sections(fpath)
        if sections:
            section_map[fname] = sections
    return section_map

def resolve_shorthand(target_str, current_file):
    """Resolve shorthand references like '10 §6' or '13 §4.2' to a filename."""
    m = re.match(r'(\d+(?:\.\d+)?)\s+§', target_str)
    if m:
        prefix = m.group(1)
        files = sorted(os.listdir(SPECS_DIR))
        # First try exact prefix match (e.g., "21" -> "21-ADR-决策记录.md")
        for fname in files:
            if fname.startswith(prefix + '-') and fname.endswith('.md'):
                return fname
        # Then try sub-prefix match (e.g., "21.06" -> "21.06-Contract.md")
        for fname in files:
            if fname.startswith(prefix + '.') and fname.endswith('.md'):
                return fname
    return None

def check_references():
    """Check all § references in main specs files."""
    section_map = build_section_map()
    issues = []
    
    # Regex for § references
    ref_re = re.compile(r'§([一二三四五六七八九十\d]+(?:\.\d+)*)')
    
    for fname in sorted(os.listdir(SPECS_DIR)):
        if not fname.endswith('.md'):
            continue
        fpath = os.path.join(SPECS_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        
        file_sections = section_map.get(fname, set())
        
        with open(fpath, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Find all § references in the line
            for m in ref_re.finditer(line):
                ref_text = m.group(1)
                
                # Check for Chinese numerals
                cn_match = re.match(r'[一二三四五六七八九十]', ref_text)
                if cn_match:
                    issues.append((fname, i, 'CHINESE_NUM', ref_text, m.group(0)))
                    continue
                
                # Check if it's an internal reference
                # First, try to determine if there's an external file reference
                # Look for `specs/XX.md` or shorthand before this §
                before = line[:m.start()]
                
                # Check for explicit file reference: `specs/XX.md`
                ext_m = re.search(r'`specs/([^`]+\.md)`\s*$', before)
                if ext_m:
                    target_file = ext_m.group(1)
                    if target_file in section_map:
                        target_sections = section_map[target_file]
                        if ref_text not in target_sections:
                            issues.append((fname, i, 'MISSING_EXT', f'{target_file} §{ref_text}', m.group(0)))
                    else:
                        issues.append((fname, i, 'FILE_NOT_FOUND', target_file, m.group(0)))
                    continue
                
                # Check for shorthand reference: NN §N or NN.NN §N
                # Look for pattern like "10 §6" or "13 §4.2" before the §
                shorthand_m = re.search(r'(\d+(?:\.\d+)?)\s+$', before)
                if shorthand_m:
                    prefix = shorthand_m.group(1)
                    target_file = resolve_shorthand(f'{prefix} §', fname)
                    if target_file and target_file in section_map:
                        target_sections = section_map[target_file]
                        if ref_text not in target_sections:
                            issues.append((fname, i, 'MISSING_SHORTHAND', f'{target_file} §{ref_text}', m.group(0)))
                    elif not target_file:
                        issues.append((fname, i, 'SHORTHAND_UNRESOLVED', f'{prefix} §{ref_text}', m.group(0)))
                    continue
                
                # Check for internal reference with "本文" prefix
                if '本文' in before:
                    if ref_text not in file_sections:
                        issues.append((fname, i, 'MISSING_INTERNAL', f'§{ref_text}', m.group(0)))
                    continue
                
                # Default: treat as internal reference
                if ref_text not in file_sections:
                    issues.append((fname, i, 'MISSING_INTERNAL', f'§{ref_text}', m.group(0)))
    
    return issues

def main():
    issues = check_references()
    
    if not issues:
        print("所有 § 引用检查通过，未发现问题。")
        return 0
    
    print(f"§ 引用检查发现 {len(issues)} 个问题：\n")
    
    for fname, line, issue_type, detail, original in issues:
        type_desc = {
            'CHINESE_NUM': '中文数字 § 引用',
            'MISSING_EXT': '指向不存在的章节',
            'MISSING_SHORTHAND': '速记引用指向不存在的章节',
            'MISSING_INTERNAL': '内部引用指向不存在的章节',
            'FILE_NOT_FOUND': '引用文件不存在',
            'SHORTHAND_UNRESOLVED': '速记引用无法解析目标文件',
        }
        print(f"  {fname}:{line}: [{type_desc.get(issue_type, issue_type)}] {detail} (原始: {original})")
    
    return 1

if __name__ == '__main__':
    sys.exit(main())