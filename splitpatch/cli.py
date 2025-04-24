#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from typing import List

from splitpatch.patch import Patch
from splitpatch.tree import DirNode
from splitpatch.merge import Merge
from splitpatch import __version__, logger, setup_logging


def setup_args() -> argparse.Namespace:
    """Set up and validate command line arguments

    Includes:
    1. Parse command line arguments
    2. Validate argument validity
    3. Configure logging level
    4. Print argument information

    Returns:
        argparse.Namespace: Parsed argument object
    """
    parser = argparse.ArgumentParser(description='Split patch tool')

    # Base parameters
    parser.add_argument('patch_files', type=str, nargs='+', help='Input patch file paths, multiple files can be specified')
    parser.add_argument('--out-dir', type=str, help='Output directory path')

    # Split parameters
    parser.add_argument('--level', type=int, default=1, help='Merge level limit (default: 1)')
    parser.add_argument('--threshold', type=int, default=10,
                        help='Module change file count threshold, merge to parent directory if below this value (default: 10)')

    # Other parameters
    parser.add_argument('--dry-run', action='store_true', help='Only show operations to be performed, do not execute')
    parser.add_argument('--log-level', type=str, default='WARNING',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level (default: WARNING)')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    args = parser.parse_args()
    # Validate arguments
    if not args.dry_run and not args.out_dir:
        parser.error("--out-dir is required in non-dry-run mode")

    # Configure logging
    setup_logging(args.log_level)
    logger.debug("Starting to process patch files")

    # Print argument information
    logger.info("Current arguments:")
    logger.info(f"  Input files: {', '.join(args.patch_files)}")
    if args.out_dir:
        logger.info(f"  Output directory: {args.out_dir}")
    logger.info(f"  Merge level: {args.level}")
    logger.info(f"  File count threshold: {args.threshold}")
    logger.info(f"  Log level: {args.log_level}")
    logger.info(f"  Dry run: {'yes' if args.dry_run else 'no'}")

    return args


def parse_patches(patch_files: List[str]) -> Patch:
    """Parse and validate all patch files

    Args:
        patch_files: List of patch file paths

    Returns:
        Patch: Combined patch object

    Raises:
        SystemExit: When invalid patch files are found
    """
    logger.debug("Starting to parse patch files")
    combined_patch = Patch("combined.patch")
    invalid_files = []

    for patch_file in patch_files:
        patch = Patch(patch_file)
        if not patch.is_valid():
            invalid_files.append(patch_file)
            continue

        logger.debug(f"Parsing patch file: {patch_file}")
        patch.parse_patch()

        # Merge into combined data
        for file_path, changes in patch.items():
            if file_path in combined_patch:
                # If file exists, extend content
                combined_patch[file_path].extend(changes)
            else:
                combined_patch[file_path] = changes

    if invalid_files:
        logger.error("The following patch files are invalid:")
        for file in invalid_files:
            logger.error(f"  - {file}")
        sys.exit(1)

    logger.debug(f"All patch files parsed: {combined_patch}")
    return combined_patch

def split_patch(patch: Patch, level: int, threshold: int) -> List[Patch]:
    """Split and merge patch data based on level and threshold parameters

    Args:
        patch: Patch object to be processed
        level: Level limit for merging
        threshold: File count threshold for module merging

    Returns:
        List[Patch]: List of merged patches
    """
    logger.debug("Processing patch data")

    # Build file tree
    root = DirNode.from_patch(patch)
    logger.debug(f"Built file tree structure:\n{root}")

    # Apply merge strategy
    strategy = Merge(root, level, threshold)
    strategy.merge()
    logger.debug(f"Merged file tree structure:\n{root}")

    # Convert merged tree to patch list
    return root.to_patches()


def output_patches(patches: List[Patch], out_dir: str, dry_run: bool) -> None:
    """Output processed patches to specified directory

    Args:
        patches: List of patches to output
        out_dir: Output directory path
        dry_run: If True, only print info without actually writing files
    """
    if dry_run:
        logger.info("Dry run mode - files will not be written")
        for i, patch in enumerate(patches, 1):
            normalized_path = patch.path.lstrip('/').replace('/', '_')
            logger.info(f"Patch {i:03d}_{normalized_path}.patch")
        return

    os.makedirs(out_dir, exist_ok=True)
    for i, patch in enumerate(patches, 1):
        normalized_path = patch.path.lstrip('/').replace('/', '_')
        output_file = os.path.join(out_dir, f"{i:03d}_{normalized_path}.patch")

        try:
            patch.path = output_file
            patch.write_patch()
            logger.info(f"Output file: {patch}")
        except IOError as e:
            logger.error(f"Failed to write file {output_file}: {e}")
            sys.exit(1)


def main() -> None:
    try:
        # Parse command line arguments
        args = setup_args()

        # Parse patch files
        combined_patch = parse_patches(args.patch_files)

        # Process patch data
        patches = split_patch(combined_patch, args.level, args.threshold)

        # Output results
        output_patches(patches, args.out_dir, args.dry_run)

    except Exception as e:
        logger.error(f"An error occurred during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()