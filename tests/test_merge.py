#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from splitpatch.tree import DirNode, FileDiff
from splitpatch.merge import Merge

class TestMerge(unittest.TestCase):
    def setUp(self):
        # Create a complex file tree structure to trigger all three merge conditions
        self.root = DirNode("/")

        # Add all files (only through root node)
        self.root.add_file(FileDiff.from_dict("file1.txt", ["diff content 1"]))
        self.root.add_file(FileDiff.from_dict("file2.txt", ["diff content 2"]))
        self.root.add_file(FileDiff.from_dict("dir1/file3.txt", ["diff content 3"]))
        self.root.add_file(FileDiff.from_dict("dir1/file4.txt", ["diff content 4"]))
        self.root.add_file(FileDiff.from_dict("dir1/dir1_sub/file5.txt", ["diff content 5"]))
        self.root.add_file(FileDiff.from_dict("dir2/file6.txt", ["diff content 6"]))
        self.root.add_file(FileDiff.from_dict("dir2/dir2_sub/file7.txt", ["diff content 7"]))
        self.root.add_file(FileDiff.from_dict("dir3/dir3_sub/file8.txt", ["diff content 8"]))
        self.root.add_file(FileDiff.from_dict("dir4/file9.txt", ["diff content 9"]))
        self.root.add_file(FileDiff.from_dict("dir5/dir5_sub/file10.txt", ["diff content 10"]))
        self.root.add_file(FileDiff.from_dict("dir5/dir5_sub/dir5_sub_sub/file11.txt", ["diff content 11"]))

        # Save directory node references for testing
        self.dir1 = next(node for node in self.root.dir_nodes if node.name == "dir1")
        self.dir1_sub = next(node for node in self.dir1.dir_nodes if node.name == "dir1_sub")
        self.dir2 = next(node for node in self.root.dir_nodes if node.name == "dir2")
        self.dir2_sub = next(node for node in self.dir2.dir_nodes if node.name == "dir2_sub")
        self.dir3 = next(node for node in self.root.dir_nodes if node.name == "dir3")
        self.dir3_sub = next(node for node in self.dir3.dir_nodes if node.name == "dir3_sub")
        self.dir4 = next(node for node in self.root.dir_nodes if node.name == "dir4")
        self.dir5 = next(node for node in self.root.dir_nodes if node.name == "dir5")
        self.dir5_sub = next(node for node in self.dir5.dir_nodes if node.name == "dir5_sub")
        self.dir5_sub_sub = next(node for node in self.dir5_sub.dir_nodes if node.name == "dir5_sub_sub")

        # Create MergeStrategy instance
        self.merge_strategy = Merge(self.root, level=0, threshold=2)

    def test_merge(self):
        """Test merge strategy"""

        # Step 1: Verify module boundary nodes
        self.assertFalse(self.merge_strategy._is_module_boundary(self.dir1))
        self.assertFalse(self.merge_strategy._is_module_boundary(self.dir2))
        self.assertTrue(self.merge_strategy._is_module_boundary(self.dir3_sub))
        self.assertTrue(self.merge_strategy._is_module_boundary(self.dir5_sub))

        # Verify initial state
        self.assertEqual(len(self.root.file_changes), 2)  # file1.txt, file2.txt
        self.assertEqual(len(self.root.dir_nodes), 5)  # dir1, dir2, dir3, dir4, dir5
        self.assertEqual(len(self.dir1.file_changes), 2)  # file3.txt, file4.txt
        self.assertEqual(len(self.dir1.dir_nodes), 1)  # dir1_sub
        self.assertEqual(len(self.dir2.file_changes), 1)  # file6.txt
        self.assertEqual(len(self.dir2.dir_nodes), 1)  # dir2_sub
        self.assertEqual(len(self.dir3.file_changes), 0)
        self.assertEqual(len(self.dir3.dir_nodes), 1)  # dir3_sub
        self.assertEqual(len(self.dir4.file_changes), 1)  # file9.txt
        self.assertEqual(len(self.dir5.file_changes), 0)
        self.assertEqual(len(self.dir5.dir_nodes), 1)  # dir5_sub

        # Execute merge strategy
        self.merge_strategy.merge()

        # Step 2: Verify flatten operation results
        # Check dir1 state
        self.assertEqual(len(self.dir1.file_changes), 3)  # file3.txt, file4.txt, file5.txt
        self.assertEqual(len(self.dir1.dir_nodes), 0)  # dir1_sub removed
        self.assertTrue(any(f.path == "dir1/dir1_sub/file5.txt" for f in self.dir1.file_changes))

        # Check dir2 state
        self.assertEqual(len(self.dir2.file_changes), 2)  # file6.txt, file7.txt
        self.assertEqual(len(self.dir2.dir_nodes), 0)  # dir2_sub removed
        self.assertTrue(any(f.path == "dir2/dir2_sub/file7.txt" for f in self.dir2.file_changes))

        # Check dir5 state
        self.assertEqual(len(self.dir5.file_changes), 2)  # file10.txt, file11.txt
        self.assertEqual(len(self.dir5.dir_nodes), 0)  # dir5_sub removed
        self.assertTrue(any(f.path == "dir5/dir5_sub/file10.txt" for f in self.dir5.file_changes))
        self.assertTrue(any(f.path == "dir5/dir5_sub/dir5_sub_sub/file11.txt" for f in self.dir5.file_changes))

        # Step 3: Verify shorten_paths operation results
        # Check dir3 state (should be merged into root)
        self.assertEqual(len(self.root.file_changes), 4)  # file1.txt, file2.txt, file8.txt, file9.txt
        self.assertTrue(any(f.path == "dir3/dir3_sub/file8.txt" for f in self.root.file_changes))
        self.assertTrue(any(f.path == "dir4/file9.txt" for f in self.root.file_changes))
        self.assertEqual(len(self.root.dir_nodes), 3)  # dir1, dir2, dir5

        # Step 4: Verify merge_by_level_and_size operation results
        # Check final state
        self.assertEqual(len(self.root.file_changes), 4)  # file1.txt, file2.txt, file8.txt, file9.txt
        self.assertEqual(len(self.root.dir_nodes), 3)  # dir1, dir2, dir5

        # Check dir1 final state (file count above threshold, should remain independent)
        self.assertEqual(len(self.dir1.file_changes), 3)  # file3.txt, file4.txt, file5.txt
        self.assertEqual(len(self.dir1.dir_nodes), 0)

        # Check dir2 final state (file count equal to threshold, should remain independent)
        self.assertEqual(len(self.dir2.file_changes), 2)  # file6.txt, file7.txt
        self.assertEqual(len(self.dir2.dir_nodes), 0)

        # Check dir5 final state (file count equal to threshold, should remain independent)
        self.assertEqual(len(self.dir5.file_changes), 2)  # file10.txt, file11.txt
        self.assertEqual(len(self.dir5.dir_nodes), 0)

        # Verify correctness of all file paths
        expected_files = {
            "file1.txt", "file2.txt",  # /
            "dir3/dir3_sub/file8.txt", "dir4/file9.txt",  # / (merged)
            "dir1/file3.txt", "dir1/file4.txt", "dir1/dir1_sub/file5.txt",  # dir1
            "dir2/file6.txt", "dir2/dir2_sub/file7.txt",  # dir2
            "dir5/dir5_sub/file10.txt", "dir5/dir5_sub/dir5_sub_sub/file11.txt"  # dir5
        }
        actual_files = set()
        for node in [self.root, self.dir1, self.dir2, self.dir5]:
            for file_node in node.file_changes:
                actual_files.add(file_node.path)
        self.assertEqual(actual_files, expected_files)

if __name__ == "__main__":
    unittest.main()