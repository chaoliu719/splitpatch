#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import tempfile
import shutil
import os
from splitpatch.patch import Patch

class TestPatch(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()

        # Create test diff file
        self.diff_file = os.path.join(self.temp_dir, 'test.diff')
        with open(self.diff_file, 'w') as f:
            f.write('''diff --git a/file1.txt b/file1.txt
index 1234567..89abcdef 100644
--- a/file1.txt
+++ b/file1.txt
@@ -1 +1,2 @@
-test file 1
+test file 1 updated
+new line
diff --git a/dir1/file2.txt b/dir1/file2.txt
index 1234567..89abcdef 100644
--- a/dir1/file2.txt
+++ b/dir1/file2.txt
@@ -1 +1,2 @@
-test file 2
+test file 2 updated
+new line
''')

        # Create output directory
        self.output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)

    def test_is_valid(self):
        """Test patch file validity check"""
        # Test valid patch file
        patch = Patch(self.diff_file)
        self.assertTrue(patch.try_parse())

        # Test non-existent file
        non_existent = Patch(os.path.join(self.temp_dir, 'non_existent.diff'))
        self.assertFalse(non_existent.try_parse())

        # Test empty file
        empty_file = os.path.join(self.temp_dir, 'empty.diff')
        with open(empty_file, 'w') as f:
            pass
        empty_patch = Patch(empty_file)
        self.assertFalse(empty_patch.try_parse())

        # Test invalid format file
        invalid_file = os.path.join(self.temp_dir, 'invalid.diff')
        with open(invalid_file, 'w') as f:
            f.write('This is not a valid patch file')
        invalid_patch = Patch(invalid_file)
        self.assertFalse(invalid_patch.try_parse())

    def test_parse_patch(self):
        """Test patch file parsing functionality"""
        patch = Patch(self.diff_file)
        patch.try_parse()

        # Verify results
        self.assertEqual(len(patch), 2)  # Should have 2 files
        self.assertTrue('file1.txt' in patch)
        self.assertTrue('dir1/file2.txt' in patch)

        # Verify diff content
        self.assertTrue('test file 1 updated' in patch['file1.txt'])
        self.assertTrue('test file 2 updated' in patch['dir1/file2.txt'])

    def test_write_patch(self):
        """Test patch file writing functionality"""
        patch = Patch(self.diff_file)
        patch.try_parse()

        # Write to new file
        output_file = os.path.join(self.output_dir, 'output.diff')
        patch.path = output_file
        patch.write_patch()

        # Verify results
        self.assertTrue(os.path.exists(output_file))

        # Verify file content
        with open(output_file, 'r') as f:
            content = f.read()
            self.assertIn('diff --git a/file1.txt b/file1.txt', content)
            self.assertIn('diff --git a/dir1/file2.txt b/dir1/file2.txt', content)
            self.assertIn('test file 1 updated', content)
            self.assertIn('test file 2 updated', content)

    def test_str_representation(self):
        """Test string representation"""
        patch = Patch(self.diff_file)
        patch.try_parse()
        str_repr = str(patch)
        self.assertIn(self.diff_file, str_repr)
        self.assertIn('2 files', str_repr)

    def test_diff_pattern(self):
        """Test the diff pattern regex"""
        # Use the regex pattern from Patch class
        patch = Patch(self.diff_file)
        diff_pattern = patch._diff_pattern  # Assuming pattern is a class attribute

        # Test cases
        test_cases = [
            # Git style diffs (only filename)
            ('diff --git a/file.txt b/file.txt', 'file.txt'),
            ('diff --git --no-index a/file.txt b/file.txt', 'file.txt'),
            ('diff --git a/bsp/bootloader/lk/app/sprdboot/boot_parse.c b/bsp/bootloader/lk/app/sprdboot/boot_parse.c', 'bsp/bootloader/lk/app/sprdboot/boot_parse.c'),

            # Regular diffs (keep full relative path)
            ('diff -ruN old/path/to/file.c new/path/to/file.c', 'path/to/file.c'),
            ('diff --color -ruN kernel-rk/android/abi_gki_aarch64_hikey960 linux-5.10/android/abi_gki_aarch64_hikey960', 'android/abi_gki_aarch64_hikey960'),
            ('diff --color -u kernel/file.h linux/file.h', 'file.h'),
            ('diff -r original/src/main.cpp modified/src/main.cpp', 'src/main.cpp'),
            ('diff -u a/path/to/file.txt b/path/to/file.txt', 'path/to/file.txt'),

            # Invalid diff lines
            ('not a diff line', None),
            ('diff', None),
            ('diff a/file.txt', None),
            ('diff --git', None),
            ('diff --color -ruN', None),
            ('diff --color -ruN file1', None),
            # Invalid cases where paths don't match
            ('diff -u a/path/to/file1.txt b/path/to/file2.txt', None),
            ('diff -ruN old/path/to/file.c new/different/path/file.c', None),
        ]

        for test_input, expected_file in test_cases:
            match = diff_pattern.search(test_input)
            if expected_file is None:
                self.assertIsNone(match, f"Pattern should not match: {test_input}")
            else:
                self.assertIsNotNone(match, f"Pattern should match: {test_input}")
                # Get both captured paths
                path1, path2 = match.groups()
                # Verify both paths are identical
                self.assertEqual(path1, path2,
                               f"Paths should be identical, got {path1} and {path2} for input: {test_input}")
                # Verify the path matches expected
                self.assertEqual(path1, expected_file,
                               f"Expected file path {expected_file}, got {path1} for input: {test_input}")

if __name__ == "__main__":
    unittest.main()