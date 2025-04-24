#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from typing import Dict, List

from splitpatch import logger

class Patch(Dict[str, List[str]]):
    """Patch class, inherits from Dict

    key: file path
    value: list of file modifications
    """
    def __init__(self, path: str):
        """Initialize Patch

        Args:
            path: path to the patch file
        """
        super().__init__()
        self.path = path

    def is_valid(self) -> bool:
        """Check if patch file is valid

        Returns:
            bool: whether the file is valid
        """
        try:
            # Check if file exists and is readable
            if not os.path.isfile(self.path):
                return False

            # Check file size
            if os.path.getsize(self.path) == 0:
                return False

            # Read first few lines to check format
            with open(self.path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()[:10]]  # Read first 10 lines

                # Check if file is empty
                if not lines:
                    return False

                # Check common patch file identifiers
                # 1. git diff format
                if any(line.startswith('diff --git') for line in lines):
                    return True

                # 2. git commit format
                if any(line.startswith('commit ') for line in lines):
                    return True

                return False

        except (IOError, UnicodeDecodeError):
            return False

    def parse_patch(self) -> None:
        """Parse patch file and store results in dictionary"""
        logger.debug(f"Parsing patch file: {self.path}")
        current_file = None
        current_diff: List[str] = []

        with open(self.path, 'r') as f:
            for line in f:
                line = line.rstrip()

                # Check if it's a file header
                if line.startswith('diff --git'):
                    # Save previous file's diff
                    if current_file and current_diff:
                        self[current_file] = current_diff
                        current_diff = []

                    # Extract new filename
                    match = re.search(r' b/(.+)$', line)
                    if match:
                        current_file = match.group(1)
                        logger.debug(f"Found file: {current_file}")

                # Collect diff content
                if current_file:
                    current_diff.append(line)

        # Save last file's diff
        if current_file and current_diff:
            self[current_file] = current_diff

    def write_patch(self) -> None:
        """Write patch to file"""
        # Get output directory path
        output_dir = os.path.dirname(self.path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(self.path, 'w') as f:
            patch_lines = []

            # Sort by file path
            for file_path in sorted(self.keys()):
                patch_lines.extend(self[file_path])

            f.write("\n".join(patch_lines))

    def __str__(self) -> str:
        """String representation"""
        return f"{self.path} ({len(self)} files)"