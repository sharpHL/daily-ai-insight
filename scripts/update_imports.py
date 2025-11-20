#!/usr/bin/env python3
"""Script to update import statements in all Python files."""

import re
from pathlib import Path

# Define import mappings
IMPORT_MAPPINGS = {
    r'^from collectors import': 'from daily_ai_insight.collectors import',
    r'^from processors import': 'from daily_ai_insight.processors import',
    r'^from storage import': 'from daily_ai_insight.storage import',
    r'^from llm import': 'from daily_ai_insight.llm import',
    r'^from llm\.providers\.': 'from daily_ai_insight.llm.providers.',
    r'^from llm\.prompts\.': 'from daily_ai_insight.llm.prompts.',
    r'^from renderers import': 'from daily_ai_insight.renderers import',
}

def update_file_imports(file_path: Path):
    """Update imports in a single file."""
    print(f"Processing {file_path}")

    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Apply all import mappings
    for old_pattern, new_import in IMPORT_MAPPINGS.items():
        content = re.sub(old_pattern, new_import, content, flags=re.MULTILINE)

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✅ Updated {file_path}")
    else:
        print(f"  ⏭️  No changes needed for {file_path}")

def main():
    """Main function."""
    src_path = Path("src/daily_ai_insight")

    # Find all Python files
    py_files = list(src_path.rglob("*.py"))

    print(f"Found {len(py_files)} Python files to process\n")

    for py_file in py_files:
        if py_file.name != '__pycache__':
            update_file_imports(py_file)

    print("\n✅ Done!")

if __name__ == "__main__":
    main()