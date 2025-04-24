#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List

from splitpatch.tree import DirNode
from splitpatch import logger

class Merge:
    """Merge strategy class implementing three merge strategies"""

    def __init__(self, tree: DirNode, level: int, threshold: int):
        """
        Initialize merge strategy

        Args:
            tree: Root node of file tree
            level: Merge level limit
            threshold: Module change file count threshold
        """
        self.tree = tree
        self.level = level
        self.threshold = threshold

    def merge(self):
        """
        Execute merge strategy

        Returns:
            List[str]: List of merged modules, each element is a module's patch content
        """
        logger.debug("Starting merge strategy")
        logger.debug(f"Initial file tree for merge strategy: \n{self.tree}")

        # Step 1: Module-based merge
        module_nodes = self._find_module_boundaries()
        logger.debug(f"Found {len(module_nodes)} initial module boundaries")

        # Merge all nodes under module nodes
        for node in module_nodes:
            self._flatten_nodes(node)

        # Step 2: Shorten paths
        # Handle nodes with only one subdirectory and no changes
        self._shorten_paths()

        # Step 3: Level and size based merge
        self._merge_by_level_and_size()

    def _is_module_boundary(self, node: DirNode) -> bool:
        """
        Determine if node is a module boundary

        Args:
            node: Directory node

        Returns:
            bool: Whether it is a module boundary
        """
        # Module boundary conditions: current directory depth >= level and has file changes
        # and parent directory has no changes (if parent exists)
        if node.depth <= self.level:
            logger.debug(f"Node {node.path} depth {node.depth} less than level {self.level}, not a boundary")
            return False

        if not node.has_file_changes:
            logger.debug(f"Node {node.path} has no file changes, not a boundary")
            return False

        is_boundary = node.is_root or not node.parent.has_file_changes
        if is_boundary:
            logger.debug(f"Node {node.path} has no parent or parent has no changes, is a boundary")
        else:
            logger.debug(f"Node {node.path} has parent with changes, not a boundary")

        return is_boundary

    def _find_module_boundaries(self) -> List[DirNode]:
        """
        Find all module boundary nodes

        Returns:
            List[DirNode]: List of module boundary nodes
        """
        module_nodes = []

        def traverse(node: DirNode) -> None:
            if self._is_module_boundary(node):
                module_nodes.append(node)
            for child in node.dir_nodes:
                traverse(child)

        traverse(self.tree)
        logger.debug(f"Found {len(module_nodes)} module boundary nodes")
        for node in module_nodes:
            logger.debug(f"Module boundary node: {node.path}")
        return module_nodes

    def _flatten_nodes(self, node: DirNode):
        """
        All module node's children are merged into the module node

        Args:
            nodes: Initial node list
        """
        logger.debug("Starting flatten operation")
        logger.debug(f"Processing flatten for node {node.path}")

        def process_node(current: DirNode) -> None:
            """Recursively process nodes"""
            # Process all children first (bottom-up)
            for child in current.dir_nodes[:]:
                process_node(child)
                # Merge child into current node
                self._merge_to_parent(child, current)

        # Process current node
        process_node(node)
        logger.debug(f"Flatten complete, current file tree: \n{self.tree}")
        logger.debug(f"Module {node.path} processing complete, now contains {node.file_changes_count} files")

    def _shorten_paths(self):
        """
        Shorten paths by handling nodes with only one subdirectory and no changes
        """
        logger.debug("Starting path shortening operation")

        def process_node(node: DirNode) -> None:
            # Process all subdirectories first, bottom-up
            for child in node.dir_nodes[:]:
                process_node(child)

            # Skip if node depth is less than level
            if node.depth <= self.level:
                logger.debug(f"Node {node.path} depth {node.depth} less than level {self.level}, skipping")
                return
            else:
                logger.debug(f"Node {node.path} depth {node.depth} greater than or equal to level {self.level}, continuing")

            # If node has only one subdirectory and no changes
            if len(node.dir_nodes) == 1 and not node.has_file_changes:
                child = node.dir_nodes[0]
                logger.debug(f"Found path to shorten: {node.path}/[{child.name}]")
                logger.debug(f"Node {node.path} has no changes, child {child.path} will be merged")

                self._merge_to_parent(child, node)
                logger.debug(f"Path shortening complete: {child.path} -> {node.path}")
                logger.debug(f"Path shortening complete, current file tree: \n{self.tree}")

        # Start processing from root
        process_node(self.tree)
        logger.debug("Path shortening operation complete")

    def _merge_by_level_and_size(self):
        """
        Merge modules based on level and size

        Args:
            nodes: List of nodes to merge

        Returns:
            List[DirNode]: List of merged nodes
        """
        logger.debug("Starting level and size based merge")

        def process_node(node: DirNode) -> None:
            """Recursively process nodes"""
            # Process all children first (bottom-up)
            for child in node.dir_nodes[:]:
                process_node(child)

            # Skip if node depth is less than level
            if node.depth <= self.level:
                logger.debug(f"Node {node.path} depth {node.depth} less than level {self.level}, skipping")
                return
            else:
                logger.debug(f"Node {node.path} depth {node.depth} greater than or equal to level {self.level}, continuing")

            # If file count is less than threshold and has parent, merge into parent
            if node.file_changes_count < self.threshold and not node.is_root:
                logger.debug(f"Node {node.path} file count {node.file_changes_count} less than threshold {self.threshold}, merging to parent")
                self._merge_to_parent(node, node.parent)
                logger.debug(f"Merge complete, current file tree: \n{self.tree}")
                return
            else:
                logger.debug(f"Node {node.path} file count {node.file_changes_count} greater than or equal to threshold {self.threshold} (or no parent), not merging")

        # Start processing from root
        process_node(self.tree)
        logger.debug("Merge complete")

    def _merge_to_parent(self, node: DirNode, parent: DirNode) -> None:
        """
        Merge node into parent node

        Args:
            node: Node to merge
            parent: Parent node
        """
        logger.debug(f"Starting merge of node {node.path} into parent {parent.path}")
        logger.debug(f"Before merge - Parent file count: {parent.file_changes_count}, Child file count: {node.file_changes_count}")
        logger.debug(f"Before merge - Parent subdirectory count: {len(parent.dir_nodes)}, Child subdirectory count: {len(node.dir_nodes)}")

        # Move file nodes to parent
        parent.file_changes.extend(node.file_changes)
        logger.debug(f"Moved {len(node.file_changes)} file nodes to parent")

        # Move subdirectory nodes to parent
        parent.dir_nodes.extend(node.dir_nodes)
        logger.debug(f"Moved {len(node.dir_nodes)} subdirectories to parent")

        # Update parent references of subdirectories
        for child in node.dir_nodes:
            child.parent = parent
            logger.debug(f"Updated parent reference of subdirectory {child.path} to {parent.path}")

        # Clear child's subdirectory list
        node.dir_nodes = []
        logger.debug("Cleared child's subdirectory list")

        # Remove child from parent's subdirectory list
        parent.dir_nodes.remove(node)
        logger.debug(f"Removed subdirectory {node.name} from {parent.path}")

        logger.debug(f"After merge - Parent file count: {parent.file_changes_count}, Subdirectory count: {len(parent.dir_nodes)}")
        self._verify_tree_integrity(parent)
        logger.debug(f"Completed merge of node {node.path} into parent {parent.path}")

    def _verify_tree_integrity(self, node: DirNode) -> None:
        """
        Verify tree integrity, ensure all node parent-child relationships are correct

        Args:
            node: Node to verify

        Raises:
            ValueError: If tree integrity is violated
        """
        # Verify parent references of all subdirectories
        for child in node.dir_nodes:
            if child.parent != node:
                raise ValueError(f"Subdirectory {child.path} parent reference error, expected {node.path}, got {child.parent.path if child.parent else 'None'}")
            # Recursively verify subdirectories
            self._verify_tree_integrity(child)

        # Verify file node paths
        for file_node in node.file_changes:
            # Get last part of directory path as relative path
            dir_parts = node.path.split('/')
            dir_last = dir_parts[-1]

            # Check if file path contains directory path
            if dir_last not in file_node.path:
                raise ValueError(f"File node {file_node.path} path does not belong to directory {node.path}")
