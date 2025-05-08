#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from typing import Dict

from splitpatch import logger
from splitpatch.profiling import profile_method

class Patch(Dict[str, str]):
    """Patch class, inherits from Dict

    key: file path
    value: file modifications
    """
    # Define regex pattern as class attribute
    # Capture both relative paths and verify they are identical
    _diff_pattern = re.compile(r'^diff\s+(?:--?[-\w]+\s+)*[^/\s]+/([^/\s].*?)\s+[^/\s]+/(\1)$', re.MULTILINE)

    def __init__(self, path: str):
        """Initialize Patch

        Args:
            path: path to the patch file
        """
        super().__init__()
        self.path = path

    @profile_method
    def try_parse(self) -> bool:
        """Try to parse patch file and store results in dictionary

        Returns:
            bool: whether the file is valid and successfully parsed
        """
        try:
            # Check if file exists and is readable
            if not os.path.isfile(self.path):
                logger.error(f"Patch file does not exist: {self.path}")
                return False

            # Check file size
            if os.path.getsize(self.path) == 0:
                logger.error(f"Patch file is empty: {self.path}")
                return False

            # Set buffer size to 1MB for chunked reading of large files
            buffer_size = 1024 * 1024  # 1MB
            current_file = None
            current_content = []
            found_diff = False

            logger.debug(f"Starting to parse patch file: {self.path}")
            with open(self.path, 'r') as f:
                while True:
                    # Read file content in chunks
                    chunk = f.read(buffer_size)
                    if not chunk:
                        # Process content of the last file
                        if current_file and current_content:
                            self[current_file] = ''.join(current_content)
                            logger.debug(f"Completed parsing last file: {current_file}")
                        break

                    # Check if first chunk contains valid diff format
                    if not found_diff:
                        if self._diff_pattern.search(chunk):
                            found_diff = True
                            logger.debug("Found valid diff format")
                        else:
                            logger.debug(f"Invalid patch file format: {self.path}")
                            return False

                    # Find all diff markers in current chunk
                    matches = list(self._diff_pattern.finditer(chunk))
                    logger.debug(f"Found {len(matches)} diff markers in current chunk")

                    if matches:
                        for i, match in enumerate(matches):
                            if current_file:
                                # Process content of previous file
                                start_pos = 0 if i == 0 else matches[i-1].start()
                                content = chunk[start_pos:match.start()]
                                if current_content:
                                    content = ''.join(current_content) + content
                                self[current_file] = content
                                logger.debug(f"Completed parsing file: {current_file}")
                                current_content = []

                            # Start processing new file
                            current_file = match.group(1)
                            logger.debug(f"Found file: {current_file}")

                        # Save content after last diff marker
                        current_content = [chunk[matches[-1].start():]]
                    else:
                        # If no new diff markers found, append current chunk to current file content
                        if current_file:
                            current_content.append(chunk)

            logger.debug(f"Patch file parsing completed, parsed {len(self)} files")
            return True

        except (IOError, UnicodeDecodeError):
            logger.error(f"Error reading patch file: {self.path}")
            return False

    @profile_method
    def write_patch(self):
        """Write patch to file"""
        # Get output directory path
        output_dir = os.path.dirname(self.path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(self.path, 'w') as f:
            # Sort by file path
            for file_path in sorted(self.keys()):
                f.write(self[file_path])
                f.write("\n")

    def __str__(self) -> str:
        """String representation"""
        return f"{self.path} ({len(self)} files)"