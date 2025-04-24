#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Optional

from splitpatch.patch import Patch
from splitpatch import logger

class FileDiff:
    """File node that stores file path and change content"""

    def __init__(self, path: str, changes: List[str]):
        """
        Initialize file node

        Args:
            path: File path
            changes: File change content
        """
        self.path = path
        self.changes = changes

    @classmethod
    def from_dict(cls, path: str, changes: List[str]) -> 'FileDiff':
        """Create FileDiff object from dictionary data

        Args:
            path: File path
            changes: File change content

        Returns:
            FileDiff: Newly created file node
        """
        return cls(path, changes)

class DirNode:
    """Directory node class"""

    def __init__(self, name: str, parent: Optional['DirNode'] = None):
        """
        Initialize directory node

        Args:
            name: Directory name
            parent: Parent node
        """
        self.name = name
        self.file_changes: List[FileDiff] = []  # List of file changes in current directory
        self.dir_nodes: List[DirNode] = []   # Subdirectories
        self.parent: Optional[DirNode] = parent
        self._path = name if not parent else f"{parent.path}/{name}" if parent.path != "/" else f"/{name}"
        logger.debug(f"Created node: {name} (path: {self._path})")

    def _add_file(self, file_diff: FileDiff) -> FileDiff:
        """
        Internal method: Add file to current directory node

        Args:
            file_diff: File change object

        Returns:
            FileDiff: Newly created file node
        """
        self.file_changes.append(file_diff)
        logger.debug(f"Node {self.path} added file: {file_diff.path}")
        return file_diff

    def add_file(self, file_diff: FileDiff) -> None:
        """
        Add file to tree, automatically creating necessary directory structure.
        Note: This method can only be called on the root node.

        Args:
            file_diff: File change object

        Raises:
            ValueError: If called on non-root node
        """
        if not self.is_root:
            raise ValueError("add_file method can only be called on root node")

        logger.debug(f"Adding file to tree: {file_diff.path}")
        parts = file_diff.path.split('/')
        current_node = self

        # Create directory nodes
        for i, part in enumerate(parts[:-1]):
            path = '/'.join(parts[:i+1])
            found = False

            # Check if directory node already exists
            for child in current_node.dir_nodes:
                if child.name == part:
                    current_node = child
                    found = True
                    break

            # If not found, create new node
            if not found:
                current_node = current_node.add_dir(part)
                logger.debug(f"Created new directory node: {path}")

        # Create file node and add to current directory
        current_node._add_file(file_diff)
        logger.debug(f"Created file node: {file_diff.path}")

    def add_dir(self, name: str) -> 'DirNode':
        """
        Add subdirectory node

        Args:
            name: Subdirectory name

        Returns:
            DirNode: Newly created subdirectory node
        """
        child = DirNode(name, parent=self)
        self.dir_nodes.append(child)
        logger.debug(f"Node {self.path} added subdirectory: {child.path}")
        return child

    @property
    def is_root(self) -> bool:
        """Check if node is root node"""
        return self.parent is None

    @property
    def path(self) -> str:
        """Get node path"""
        return self._path

    @property
    def depth(self) -> int:
        """Get node depth level"""
        depth = 0
        current = self
        while current.parent:
            depth += 1
            current = current.parent
        logger.debug(f"Node {self.path} depth is {depth}")
        return depth

    @property
    def has_file_changes(self) -> bool:
        """Check if node has file changes, excluding subdirectories"""
        return len(self.file_changes) > 0

    @property
    def file_changes_count(self) -> int:
        """Get number of file changes, excluding subdirectories"""
        return len(self.file_changes)

    def __str__(self) -> str:
        """String representation, recursively showing directory structure"""
        def _tree_str(node: DirNode, level: int = 0, prefix: str = "", is_last: bool = True) -> str:
            # Current node representation
            node_str = f"{prefix}{'└── ' if level > 0 else ''}{node.name}"
            node_str += f" ({len(node.file_changes)} files)"
            result = [node_str]

            # Only show directory nodes
            for i, dir_node in enumerate(node.dir_nodes):
                is_last_dir = i == len(node.dir_nodes) - 1
                child_prefix = prefix + ("" if level == 0 else "│   " if not is_last else "    ")
                result.append(_tree_str(dir_node, level + 1, child_prefix, is_last_dir))

            return "\n".join(result)

        return _tree_str(self)

    def to_patches(self) -> List[Patch]:
        """
        Convert directory tree to patch list

        Returns:
            List[Patch]: List of patches, each representing a module's changes
        """
        patches = []

        def _collect_patches(node: DirNode) -> None:
            if node.file_changes:  # Only process nodes with files
                patch = Patch(f"{node.path}")
                for file_diff in node.file_changes:
                    patch[file_diff.path] = file_diff.changes
                patches.append(patch)
            for child in node.dir_nodes:
                _collect_patches(child)

        _collect_patches(self)
        return patches

    @classmethod
    def from_patch(cls, patch: Patch) -> 'DirNode':
        """Create directory tree from patch file

        Args:
            patch: Patch object containing file paths and changes

        Returns:
            DirNode: Created directory tree root node
        """
        root = cls("/")
        for file_path, changes in patch.items():
            file_diff = FileDiff.from_dict(file_path, changes)
            root.add_file(file_diff)
        return root
