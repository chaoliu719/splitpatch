import unittest
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock

# Import modules to be tested
from splitpatch.cli import setup_args, parse_patches, split_patch, output_patches, main
from splitpatch.patch import Patch

class TestCLI(unittest.TestCase):

    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.sample_patch_content = """diff --git a/file1.py b/file1.py
--- a/file1.py
+++ b/file1.py
@@ -1,5 +1,6 @@
 def func():
-    return 1
+    # Added comment
+    return 2

diff --git a/dir1/file2.py b/dir1/file2.py
--- a/dir1/file2.py
+++ b/dir1/file2.py
@@ -10,7 +10,7 @@
 class Test:
     def method(self):
-        print("old")
+        print("new")
"""
        self.sample_patch_file = os.path.join(self.temp_dir, "test.patch")
        with open(self.sample_patch_file, 'w') as f:
            f.write(self.sample_patch_content)

    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary files and directory
        if os.path.exists(self.sample_patch_file):
            os.remove(self.sample_patch_file)
        os.rmdir(self.temp_dir)

    @patch('sys.argv', ['splitpatch', 'test.patch', '--outdir', 'output', '--log-level', 'DEBUG'])
    def test_setup_args(self):
        """Test command line argument parsing"""
        args = setup_args()
        self.assertEqual(args.patch_files, ['test.patch'])
        self.assertEqual(args.outdir, 'output')
        self.assertEqual(args.log_level, 'DEBUG')
        self.assertEqual(args.level, 1)  # Default value
        self.assertEqual(args.threshold, 10)  # Default value
        self.assertFalse(args.dry_run)

    @patch('sys.argv', ['splitpatch', 'test.patch', '--dry-run'])
    def test_setup_args_dry_run(self):
        """Test dry run mode arguments"""
        args = setup_args()
        self.assertTrue(args.dry_run)
        self.assertIsNone(args.outdir)  # Output directory is optional in dry run mode

    @patch('sys.argv', ['splitpatch', 'test.patch'])
    @patch('sys.exit')
    def test_setup_args_missing_outdir(self, mock_exit):
        """Test error handling for missing required arguments"""
        # Output directory is required in non-dry run mode
        setup_args()
        mock_exit.assert_called_once()

    def test_parse_patches_valid(self):
        """Test parsing valid patch file"""
        patch = parse_patches([self.sample_patch_file])
        self.assertIsInstance(patch, Patch)
        self.assertEqual(len(patch), 2)  # Two file modifications
        self.assertIn('file1.py', patch)
        self.assertIn('dir1/file2.py', patch)

    @patch('sys.exit')
    def test_parse_patches_invalid(self, mock_exit):
        """Test parsing invalid patch file"""
        # Create an empty file as invalid patch
        invalid_patch = os.path.join(self.temp_dir, "invalid.patch")
        with open(invalid_patch, 'w') as f:
            f.write("")

        try:
            parse_patches([invalid_patch])
            mock_exit.assert_called_once()
        finally:
            if os.path.exists(invalid_patch):
                os.remove(invalid_patch)

    def test_split_patch(self):
        """Test patch splitting functionality"""
        patch = Patch(self.sample_patch_file)
        patch.parse_patch()

        # Test splitting with default parameters
        patches = split_patch(patch, level=1, threshold=10)
        self.assertIsInstance(patches, list)
        # Based on sample patch content, should split into two patches
        # One for root directory's file1.py, one for dir1/file2.py
        self.assertEqual(len(patches), 2)

    def test_output_patches_normal(self):
        """Test patch output functionality"""
        patch1 = Patch("file1.py")
        patch1["file1.py"] = ["diff --git a/file1.py b/file1.py", "--- a/file1.py", "+++ b/file1.py"]

        patch2 = Patch("dir1/file2.py")
        patch2["dir1/file2.py"] = ["diff --git a/dir1/file2.py b/dir1/file2.py", "--- a/dir1/file2.py", "+++ b/dir1/file2.py"]

        patches = [patch1, patch2]

        # Use mock_open to simulate file writing
        with patch('builtins.open', mock_open()) as mocked_file:
            with patch('os.makedirs') as mock_makedirs:
                output_patches(patches, "output_dir", dry_run=False)
                # Check if makedirs was called at least once
                mock_makedirs.assert_called()
                # Check if files were written
                self.assertGreater(mocked_file.call_count, 0)

    def test_output_patches_dry_run(self):
        """Test patch output in dry run mode"""
        patch1 = Patch("file1.py")
        patch2 = Patch("dir1/file2.py")
        patches = [patch1, patch2]

        # Use mock to capture log output
        with patch('splitpatch.logger.info') as mock_logger:
            output_patches(patches, "output_dir", dry_run=True)

            # Check log calls
            mock_logger.assert_any_call("Dry run mode - files will not be written")

            # Ensure no directories are created in dry run mode
            with patch('os.makedirs') as mock_makedirs:
                output_patches(patches, "output_dir", dry_run=True)
                mock_makedirs.assert_not_called()

    @patch('splitpatch.cli.setup_args')
    @patch('splitpatch.cli.parse_patches')
    @patch('splitpatch.cli.split_patch')
    @patch('splitpatch.cli.output_patches')
    def test_main_function(self, mock_output, mock_split, mock_parse, mock_setup):
        """Test main function workflow"""
        # Mock command line arguments
        args = MagicMock()
        args.patch_files = [self.sample_patch_file]
        args.outdir = "output"
        args.level = 1
        args.threshold = 10
        args.dry_run = False
        mock_setup.return_value = args

        # Mock patch parsing
        mock_patch = MagicMock()
        mock_parse.return_value = mock_patch

        # Mock patch splitting
        mock_patches = [MagicMock(), MagicMock()]
        mock_split.return_value = mock_patches

        # Execute main function
        main()

        # Verify call chain
        mock_setup.assert_called_once()
        mock_parse.assert_called_once_with([self.sample_patch_file])
        mock_split.assert_called_once_with(mock_patch, 1, 10)
        mock_output.assert_called_once_with(mock_patches, "output", False)

    @patch('sys.exit')
    def test_main_exception_handling(self, mock_exit):
        """Test main function exception handling"""
        # Mock exception scenario
        with patch('splitpatch.cli.setup_args', side_effect=Exception("Test error")):
            main()
            mock_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()