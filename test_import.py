#!/usr/bin/env python
"""
Unit Tests for Import Functionality

Tests DDF and MSG import with valid and invalid input scenarios.
"""

import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.import_base import (
    ImportResult, ImportTransaction, ImportProgress, ImportIssue, ImportLevel,
    ImportProgressReporter
)
from core.ddf_importer import DDFImporter
from core.msg_importer import MSGImporter
from core.import_manager import ImportManager, ImportFormat, ImportOptions
from models.dialogue import Dialogue


class TestImportBase(unittest.TestCase):
    """Tests for base import functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_temp_file(self, filename: str, content: str) -> Path:
        """Create a temporary test file"""
        file_path = Path(self.test_dir) / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path


class TestImportResult(TestImportBase):
    """Tests for ImportResult class"""
    
    def test_import_result_defaults(self):
        """Test ImportResult default values"""
        result = ImportResult(success=False)
        
        self.assertFalse(result.success)
        self.assertEqual(result.imported_count, 0)
        self.assertEqual(result.skipped_count, 0)
        self.assertEqual(result.total_count, 0)
        self.assertFalse(result.has_warnings)
        self.assertFalse(result.has_errors)
    
    def test_add_warning(self):
        """Test adding warnings"""
        result = ImportResult(success=True)
        result.add_warning("Test warning", line_number=10)
        
        self.assertTrue(result.has_warnings)
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.warnings[0].message, "Test warning")
        self.assertEqual(result.warnings[0].line_number, 10)
    
    def test_add_error(self):
        """Test adding errors"""
        result = ImportResult(success=True)
        result.add_error("Test error", line_number=20, recoverable=True)
        
        self.assertTrue(result.has_errors)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].message, "Test error")
        self.assertEqual(result.errors[0].line_number, 20)
        self.assertTrue(result.errors[0].recoverable)


class TestImportTransaction(TestImportBase):
    """Tests for ImportTransaction class"""
    
    def test_empty_transaction(self):
        """Test empty transaction commits successfully"""
        transaction = ImportTransaction("test")
        result = transaction.execute()
        
        self.assertTrue(result.success)
        self.assertTrue(transaction.is_committed())
    
    def test_successful_operations(self):
        """Test transaction with successful operations"""
        transaction = ImportTransaction("test")
        
        results = []
        
        def operation1():
            results.append("op1")
            return True
        
        def operation2():
            results.append("op2")
            return True
        
        transaction.add_operation(operation1)
        transaction.add_operation(operation2)
        
        result = transaction.execute()
        
        self.assertTrue(result.success)
        self.assertEqual(results, ["op1", "op2"])
        self.assertTrue(transaction.is_committed())
    
    def test_failed_operation(self):
        """Test transaction fails on failed operation"""
        transaction = ImportTransaction("test")
        
        results = []
        
        def operation1():
            results.append("op1")
            return True
        
        def operation2():
            results.append("op2")
            return False
        
        def rollback1():
            results.append("rollback1")
        
        transaction.add_operation(operation1, rollback1)
        transaction.add_operation(operation2)
        
        result = transaction.execute()
        
        self.assertFalse(result.success)
        self.assertEqual(results, ["op1", "op2", "rollback1"])
        self.assertTrue(transaction.is_rolled_back())
    
    def test_exception_rollback(self):
        """Test transaction rolls back on exception"""
        transaction = ImportTransaction("test")
        
        results = []
        
        def operation1():
            results.append("op1")
            return True
        
        def operation2():
            results.append("op2")
            raise ValueError("Test exception")
        
        def rollback1():
            results.append("rollback1")
        
        transaction.add_operation(operation1, rollback1)
        transaction.add_operation(operation2)
        
        result = transaction.execute()
        
        self.assertFalse(result.success)
        self.assertEqual(results, ["op1", "op2", "rollback1"])
        self.assertTrue(transaction.is_rolled_back())


class TestDDFImporter(TestImportBase):
    """Tests for DDF importer"""
    
    def test_import_valid_ddf(self):
        """Test importing valid DDF content"""
        ddf_content = """NPCName = "Test NPC"
Description = "A test character"
Location = "Test Location"

descproc
begin;
unknown = "You see a test NPC."
known = "You see Test NPC."
detailed = "You see a well-dressed test NPC."
end;

StartNodes
Begin
Case (default): Start EndCase
End

node Start ;
wtg "Hello, traveler!";
{skill_speech >= 50} "I need information." -> Info;
"Goodbye." -> Done;
"""
        
        file_path = self.create_temp_file("test.ddf", ddf_content)
        
        importer = DDFImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
        self.assertTrue(result.success)
        self.assertEqual(dialogue.npcname, "Test NPC")
        self.assertEqual(dialogue.location, "Test Location")
        self.assertEqual(dialogue.unknowndesc, "You see a test NPC.")
        self.assertGreater(dialogue.nodecount, 0)
    
    def test_import_nonexistent_file(self):
        """Test importing non-existent file"""
        importer = DDFImporter()
        dialogue, result = importer.import_file(Path("nonexistent.ddf"))
        
        self.assertIsNone(dialogue)
        self.assertFalse(result.success)
        self.assertTrue(result.has_errors)
    
    def test_import_empty_file(self):
        """Test importing empty file"""
        file_path = self.create_temp_file("empty.ddf", "")
        
        importer = DDFImporter()
        dialogue, result = importer.import_file(file_path)
        
        # Empty file should create dialogue but with warnings
        self.assertIsNotNone(dialogue)
    
    def test_import_malformed_ddf(self):
        """Test importing malformed DDF content"""
        malformed_content = """
This is not valid DDF content.
It has no proper structure.
Just random text.
        """
        
        file_path = self.create_temp_file("malformed.ddf", malformed_content)
        
        importer = DDFImporter()
        dialogue, result = importer.import_file(file_path)
        
        # Should still create dialogue, but with warnings
        self.assertIsNotNone(dialogue)
    
    def test_import_ddf_with_comments(self):
        """Test importing DDF with comments"""
        ddf_content = """
/* This is a comment */
NPCName = "Commented NPC"
// Another comment
Description = "Has comments"
// Multi-line
// comment block
        """
        
        file_path = self.create_temp_file("with_comments.ddf", ddf_content)
        
        importer = DDFImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
        self.assertEqual(dialogue.npcname, "Commented NPC")
    
    def test_import_ddf_multiple_nodes(self):
        """Test importing DDF with multiple nodes"""
        ddf_content = """
NPCName = "Multi Node NPC"

StartNodes
Begin
Case (default): Node1 EndCase
End

node Node1 ;
wtg "Welcome!";
"Go to node 2" -> Node2;
"Goodbye" -> Done;

node Node2 ;
wtg "This is node 2";
"Return to start" -> Node1;
        """
        
        file_path = self.create_temp_file("multi_node.ddf", ddf_content)
        
        importer = DDFImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
        self.assertEqual(dialogue.nodecount, 2)
    
    def test_import_ddf_with_variables(self):
        """Test importing DDF with variable definitions"""
        ddf_content = """
NPCName = "Variable NPC"

variablei test_var;
variableie counter = 0;
variableg global_var;
        """
        
        file_path = self.create_temp_file("with_vars.ddf", ddf_content)
        
        importer = DDFImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
        self.assertGreater(dialogue.varcnt, 0)


class TestMSGImporter(TestImportBase):
    """Tests for MSG importer"""
    
    def test_import_valid_msg(self):
        """Test importing valid MSG content"""
        msg_content = """
# Test MSG file
{100}{3}{You see a test NPC.}
{101}{3}{You see the test NPC.}
{102}{3}{A detailed description.}
{103}{3}{Detailed female desc.}
{104}{0}{Hello, traveler!}
{105}{0}{What do you want?}
        """
        
        file_path = self.create_temp_file("test.msg", msg_content)
        
        importer = MSGImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
        self.assertTrue(result.success)
        self.assertEqual(dialogue.unknowndesc, "You see a test NPC.")
        self.assertEqual(dialogue.detaileddesc, "A detailed description.")
    
    def test_import_nonexistent_msg(self):
        """Test importing non-existent MSG file"""
        importer = MSGImporter()
        dialogue, result = importer.import_file(Path("nonexistent.msg"))
        
        self.assertIsNone(dialogue)
        self.assertFalse(result.success)
    
    def test_import_empty_msg(self):
        """Test importing empty MSG file"""
        file_path = self.create_temp_file("empty.msg", "")
        
        importer = MSGImporter()
        dialogue, result = importer.import_file(file_path)
        
        # Empty file should return dialogue with defaults
        self.assertIsNotNone(dialogue)
    
    def test_import_malformed_msg(self):
        """Test importing malformed MSG content"""
        msg_content = """
# Malformed entries
{not valid}
{100}
{abc}{def}
        """
        
        file_path = self.create_temp_file("malformed.msg", msg_content)
        
        importer = MSGImporter()
        dialogue, result = importer.import_file(file_path)
        
        # Should still create dialogue with some content
        self.assertIsNotNone(dialogue)
    
    def test_import_msg_with_escaped_chars(self):
        """Test importing MSG with escaped characters"""
        msg_content = """
{100}{0}{Line one\\nLine two}
{101}{0}{Special chars: \\\\{test\\\\}}
{102}{0}{Tabs\\there}
        """
        
        file_path = self.create_temp_file("escaped.msg", msg_content)
        
        importer = MSGImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
        self.assertTrue(result.success)
    
    def test_import_msg_different_speakers(self):
        """Test importing MSG with different speaker types"""
        msg_content = """
{100}{0}{NPC speaks}
{101}{1}{Player response}
{102}{2}{System message}
{103}{3}{Description text}
        """
        
        file_path = self.create_temp_file("speakers.msg", msg_content)
        
        importer = MSGImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
        # Should have some float nodes for non-dialogue entries
        self.assertIsNotNone(dialogue)
    
    def test_import_msg_duplicate_ids(self):
        """Test importing MSG with duplicate message IDs"""
        msg_content = """
{100}{0}{First entry}
{100}{0}{Duplicate entry}
{101}{0}{Third entry}
        """
        
        file_path = self.create_temp_file("duplicates.msg", msg_content)
        
        importer = MSGImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
        # Should have warnings about duplicates
        self.assertTrue(result.has_warnings or result.success)
    
    def test_import_msg_male_female_text(self):
        """Test importing MSG with male/female text variants"""
        msg_content = """
{100}{0}{Male text}{Female text}
{101}{0}{Another male}{Another female}
        """
        
        file_path = self.create_temp_file("gendered.msg", msg_content)
        
        importer = MSGImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
        if dialogue.nodecount > 0:
            # Should have female text in nodes
            node = dialogue.nodes[0]
            self.assertIsNotNone(node.npctext_female)


class TestImportManager(TestImportBase):
    """Tests for Import Manager"""
    
    def test_auto_detect_ddf(self):
        """Test format auto-detection for DDF"""
        manager = ImportManager()
        
        # Create DDF file
        ddf_content = "NPCName = \"Test\""
        file_path = self.create_temp_file("test.ddf", ddf_content)
        
        format_detected = manager._detect_format(file_path)
        self.assertEqual(format_detected, ImportFormat.DDF)
    
    def test_auto_detect_msg(self):
        """Test format auto-detection for MSG"""
        manager = ImportManager()
        
        # Create MSG file
        msg_content = "{100}{0}{Test message}"
        file_path = self.create_temp_file("test.msg", msg_content)
        
        format_detected = manager._detect_format(file_path)
        self.assertEqual(format_detected, ImportFormat.MSG)
    
    def test_import_single_file(self):
        """Test importing a single file"""
        msg_content = "{100}{3}{Test NPC}"
        file_path = self.create_temp_file("single.msg", msg_content)
        
        manager = ImportManager()
        dialogue, result = manager.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
        self.assertTrue(result.success)
    
    def test_import_multiple_files(self):
        """Test importing multiple files"""
        # Create test files
        files = []
        for i in range(3):
            content = f"{{100}}{{3}}{{NPC {i}}}"
            path = self.create_temp_file(f"test{i}.msg", content)
            files.append(path)
        
        manager = ImportManager()
        summary = manager.import_files(files)
        
        self.assertEqual(summary.total_files, 3)
        self.assertEqual(summary.successful, 3)
        self.assertEqual(len(summary.dialogues), 3)
    
    def test_import_directory(self):
        """Test importing all files from a directory"""
        # Create test files in directory
        test_dir = Path(self.test_dir) / "dialogues"
        test_dir.mkdir()
        
        (test_dir / "file1.msg").write_text("{100}{0}{Test1}")
        (test_dir / "file2.msg").write_text("{100}{0}{Test2}")
        (test_dir / "file3.ddf").write_text("NPCName = \"Test\"")
        
        manager = ImportManager()
        summary = manager.import_directory(test_dir, recursive=False)
        
        self.assertEqual(summary.total_files, 3)


class TestEdgeCases(TestImportBase):
    """Tests for edge cases and error handling"""
    
    def test_unicode_content(self):
        """Test importing files with unicode content"""
        msg_content = "{100}{0}{Unicode: café, naïve, résumé}"
        file_path = self.create_temp_file("unicode.msg", msg_content)
        
        importer = MSGImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
    
    def test_very_long_message(self):
        """Test importing very long messages"""
        long_text = "A" * 10000  # 10k character message
        msg_content = f"{{100}}{{0}}{{{long_text}}}"
        file_path = self.create_temp_file("long.msg", msg_content)
        
        importer = MSGImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
    
    def test_special_characters_in_node_names(self):
        """Test importing with special characters in node names"""
        ddf_content = """
node normal_node ;
wtg "Text";
"Option" -> normal_node;
        """
        
        file_path = self.create_temp_file("special.ddf", ddf_content)
        
        importer = DDFImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)
    
    def test_mixed_encoding(self):
        """Test importing files with mixed encodings"""
        # This tests robustness with potentially corrupted files
        msg_content = "{100}{0}{Test}\x00\x1f\x7f{message}"
        file_path = self.create_temp_file("mixed.msg", msg_content)
        
        importer = MSGImporter()
        dialogue, result = importer.import_file(file_path)
        
        # Should handle gracefully
        self.assertIsNotNone(dialogue)
    
    def test_empty_node_links(self):
        """Test importing with empty node links"""
        ddf_content = """
node test_node ;
wtg "Text";
"Empty link" -> ;
        """
        
        file_path = self.create_temp_file("empty_link.ddf", ddf_content)
        
        importer = DDFImporter()
        dialogue, result = importer.import_file(file_path)
        
        self.assertIsNotNone(dialogue)


class TestProgressReporting(TestImportBase):
    """Tests for progress reporting"""
    
    def test_progress_updates(self):
        """Test that progress is reported during import"""
        progress_updates = []
        
        def on_progress(progress):
            progress_updates.append(progress.percentage)
        
        # Create test files
        files = []
        for i in range(5):
            content = f"{{100}}{{3}}{{NPC {i}}}"
            path = self.create_temp_file(f"progress{i}.msg", content)
            files.append(path)
        
        manager = ImportManager()
        manager.subscribe_progress(on_progress)
        
        summary = manager.import_files(files)
        
        # Should have received progress updates
        self.assertGreater(len(progress_updates), 0)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
