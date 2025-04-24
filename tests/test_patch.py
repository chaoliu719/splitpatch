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
        self.assertTrue(patch.is_valid())

        # Test non-existent file
        non_existent = Patch(os.path.join(self.temp_dir, 'non_existent.diff'))
        self.assertFalse(non_existent.is_valid())

        # Test empty file
        empty_file = os.path.join(self.temp_dir, 'empty.diff')
        with open(empty_file, 'w') as f:
            pass
        empty_patch = Patch(empty_file)
        self.assertFalse(empty_patch.is_valid())

        # Test invalid format file
        invalid_file = os.path.join(self.temp_dir, 'invalid.diff')
        with open(invalid_file, 'w') as f:
            f.write('This is not a valid patch file')
        invalid_patch = Patch(invalid_file)
        self.assertFalse(invalid_patch.is_valid())

    def test_parse_patch(self):
        """Test patch file parsing functionality"""
        patch = Patch(self.diff_file)
        patch.parse_patch()

        # Verify results
        self.assertEqual(len(patch), 2)  # Should have 2 files
        self.assertTrue('file1.txt' in patch)
        self.assertTrue('dir1/file2.txt' in patch)

        # Verify diff content
        self.assertTrue(any('test file 1 updated' in line for line in patch['file1.txt']))
        self.assertTrue(any('test file 2 updated' in line for line in patch['dir1/file2.txt']))

    def test_write_patch(self):
        """Test patch file writing functionality"""
        patch = Patch(self.diff_file)
        patch.parse_patch()

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
        patch.parse_patch()
        str_repr = str(patch)
        self.assertIn(self.diff_file, str_repr)
        self.assertIn('2 files', str_repr)

if __name__ == "__main__":
    unittest.main()