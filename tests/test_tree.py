#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from splitpatch.tree import DirNode, FileDiff
from splitpatch.patch import Patch

class TestDirTree(unittest.TestCase):
    def setUp(self):
        # Build test data using internal interface
        self.root = DirNode("/")

        # Add all files (only through root node)
        self.root.add_file(FileDiff.from_dict("file1.txt", ["diff content 1"]))
        self.root.add_file(FileDiff.from_dict("file2.txt", ["diff content 2"]))
        self.root.add_file(FileDiff.from_dict("dir1/file3.txt", ["diff content 3"]))
        self.root.add_file(FileDiff.from_dict("dir1/file4.txt", ["diff content 4"]))
        self.root.add_file(FileDiff.from_dict("dir1/dir2/file5.txt", ["diff content 5"]))
        self.root.add_file(FileDiff.from_dict("dir1/dir2/file6.txt", ["diff content 6"]))
        self.root.add_file(FileDiff.from_dict("dir1/dir2/dir3/file7.txt", ["diff content 7"]))
        self.root.add_file(FileDiff.from_dict("dir4/file8.txt", ["diff content 8"]))
        self.root.add_file(FileDiff.from_dict("dir4/dir5/file9.txt", ["diff content 9"]))
        self.root.add_file(FileDiff.from_dict("dir6/dir7/file10.txt", ["diff content 10"]))
        self.root.add_file(FileDiff.from_dict("dir6/dir7/file11.txt", ["diff content 11"]))
        self.root.add_file(FileDiff.from_dict("dir8/file12.txt", ["diff content 12"]))
        self.root.add_file(FileDiff.from_dict("dir8/dir9/file13.txt", ["diff content 13"]))
        self.root.add_file(FileDiff.from_dict("dir8/dir9/file14.txt", ["diff content 14"]))
        self.root.add_file(FileDiff.from_dict("dir10/dir11/file15.txt", ["diff content 15"]))
        self.root.add_file(FileDiff.from_dict("dir10/dir12/file16.txt", ["diff content 16"]))
        self.root.add_file(FileDiff.from_dict("dir10/dir12/file17.txt", ["diff content 17"]))

        # Save directory node references for testing
        self.dir1 = next(node for node in self.root.dir_nodes if node.name == "dir1")
        self.dir2 = next(node for node in self.dir1.dir_nodes if node.name == "dir2")
        self.dir3 = next(node for node in self.dir2.dir_nodes if node.name == "dir3")
        self.dir4 = next(node for node in self.root.dir_nodes if node.name == "dir4")
        self.dir5 = next(node for node in self.dir4.dir_nodes if node.name == "dir5")
        # ... other directory node references ...

    def test_build_tree(self):
        """Test building file tree"""
        # Check root node
        self.assertEqual(self.root.name, "/")
        self.assertEqual(self.root.path, "/")
        self.assertEqual(len(self.root.file_changes), 2)  # file1.txt, file2.txt
        self.assertEqual(len(self.root.dir_nodes), 5)  # dir1, dir4, dir6, dir8, dir10

        # Check file nodes
        file1 = next((node for node in self.root.file_changes if node.path == "file1.txt"), None)
        self.assertIsNotNone(file1)
        self.assertEqual(file1.path, "file1.txt")
        self.assertEqual(file1.changes, ["diff content 1"])

        # Check dir1 directory
        dir1 = next((node for node in self.root.dir_nodes if node.name == "dir1"), None)
        self.assertIsNotNone(dir1)
        self.assertEqual(dir1.path, "/dir1")
        self.assertEqual(len(dir1.file_changes), 2)  # dir1/file3.txt, dir1/file4.txt
        self.assertEqual(len(dir1.dir_nodes), 1)  # dir2

        # Check dir1/dir2 directory
        dir2 = next((node for node in dir1.dir_nodes if node.name == "dir2"), None)
        self.assertIsNotNone(dir2)
        self.assertEqual(dir2.path, "/dir1/dir2")
        self.assertEqual(len(dir2.file_changes), 2)  # dir1/dir2/file5.txt, dir1/dir2/file6.txt
        self.assertEqual(len(dir2.dir_nodes), 1)  # dir3

        # Check dir1/dir2/dir3 directory
        dir3 = next((node for node in dir2.dir_nodes if node.name == "dir3"), None)
        self.assertIsNotNone(dir3)
        self.assertEqual(dir3.path, "/dir1/dir2/dir3")
        self.assertEqual(len(dir3.file_changes), 1)  # dir1/dir2/dir3/file7.txt
        self.assertEqual(len(dir3.dir_nodes), 0)

    def test_to_patches(self):
        """Test conversion to patch list"""
        patches = self.root.to_patches()

        # Verify patch count
        self.assertTrue(len(patches) > 0)

        # Verify patch content
        root_patch = next((p for p in patches if p.path == "/"), None)
        self.assertIsNotNone(root_patch)
        self.assertEqual(len(root_patch), 2)  # file1.txt, file2.txt

        dir1_patch = next((p for p in patches if p.path == "/dir1"), None)
        self.assertIsNotNone(dir1_patch)
        self.assertEqual(len(dir1_patch), 2)  # file3.txt, file4.txt

    def test_from_patch(self):
        """Test conversion from patch to directory tree"""
        # Create test patch object
        test_patch = Patch("test.patch")
        test_patch["file1.txt"] = ["diff content 1"]
        test_patch["file2.txt"] = ["diff content 2"]
        test_patch["dir1/file3.txt"] = ["diff content 3"]
        test_patch["dir1/file4.txt"] = ["diff content 4"]
        test_patch["dir1/dir2/file5.txt"] = ["diff content 5"]

        # Create directory tree using from_patch
        root = DirNode.from_patch(test_patch)

        # Verify root node
        self.assertEqual(root.name, "/")
        self.assertEqual(root.path, "/")
        self.assertEqual(len(root.file_changes), 2)  # file1.txt, file2.txt
        self.assertEqual(len(root.dir_nodes), 1)     # dir1

        # Verify files in root directory
        file1 = next((f for f in root.file_changes if f.path == "file1.txt"), None)
        self.assertIsNotNone(file1)
        self.assertEqual(file1.changes, ["diff content 1"])

        file2 = next((f for f in root.file_changes if f.path == "file2.txt"), None)
        self.assertIsNotNone(file2)
        self.assertEqual(file2.changes, ["diff content 2"])

        # Verify dir1 directory
        dir1 = next((d for d in root.dir_nodes if d.name == "dir1"), None)
        self.assertIsNotNone(dir1)
        self.assertEqual(dir1.path, "/dir1")
        self.assertEqual(len(dir1.file_changes), 2)  # file3.txt, file4.txt
        self.assertEqual(len(dir1.dir_nodes), 1)     # dir2

        # Verify files in dir1
        file3 = next((f for f in dir1.file_changes if f.path == "dir1/file3.txt"), None)
        self.assertIsNotNone(file3)
        self.assertEqual(file3.changes, ["diff content 3"])

        # Verify dir1/dir2 directory
        dir2 = next((d for d in dir1.dir_nodes if d.name == "dir2"), None)
        self.assertIsNotNone(dir2)
        self.assertEqual(dir2.path, "/dir1/dir2")
        self.assertEqual(len(dir2.file_changes), 1)  # file5.txt

        # Verify files in dir2
        file5 = next((f for f in dir2.file_changes if f.path == "dir1/dir2/file5.txt"), None)
        self.assertIsNotNone(file5)
        self.assertEqual(file5.changes, ["diff content 5"])

        # Verify bidirectional conversion consistency
        patches = root.to_patches()
        self.assertTrue(any(p.path == "/" for p in patches))
        self.assertTrue(any(p.path == "/dir1" for p in patches))
        self.assertTrue(any(p.path == "/dir1/dir2" for p in patches))

if __name__ == "__main__":
    unittest.main()