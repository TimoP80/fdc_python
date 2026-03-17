"""
Unified Import Manager

Provides a unified interface for importing DDF and MSG files with:
- Auto-detection of file format
- Batch import support
- Transaction support
- Progress reporting
- Comprehensive error handling
"""

import logging
from typing import List, Optional, Dict, Any, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from core.ddf_importer import DDFImporter
from core.msg_importer import MSGImporter, Fallout2MSGImporter
from core.import_base import (
    ImportResult, ImportProgress, ImportTransaction,
    ImportProgressReporter, log_import_exception
)
from models.dialogue import Dialogue

logger = logging.getLogger(__name__)


class ImportFormat(Enum):
    """Supported import formats"""
    AUTO = "auto"
    DDF = "ddf"
    MSG = "msg"
    FMF = "fmf"  # Legacy FMF format


@dataclass
class ImportOptions:
    """Options for import operations"""
    format: ImportFormat = ImportFormat.AUTO
    encoding: str = "utf-8"
    strict_validation: bool = False
    create_backup: bool = False
    merge_existing: bool = False
    skip_duplicates: bool = True


@dataclass
class ImportSummary:
    """Summary of an import operation"""
    total_files: int
    successful: int
    failed: int
    warnings: int
    errors: int
    dialogues: List[Dialogue]
    result: ImportResult


class ImportManager:
    """
    Unified import manager for Fallout Dialogue files.
    
    Supports importing DDF, MSG, and FMF files with automatic format detection.
    """
    
    # File extension mappings
    FORMAT_EXTENSIONS = {
        ImportFormat.DDF: ['.ddf'],
        ImportFormat.MSG: ['.msg'],
        ImportFormat.FMF: ['.fmf'],
    }
    
    def __init__(self, options: Optional[ImportOptions] = None):
        self.options = options or ImportOptions()
        self.ddf_importer = DDFImporter(encoding=self.options.encoding)
        self.msg_importer = MSGImporter(encoding=self.options.encoding)
        self.progress = ImportProgressReporter()
        self._callbacks: Dict[str, Callable] = {}
    
    def import_file(self, file_path: Path, 
                   options: Optional[ImportOptions] = None) -> Tuple[Optional[Dialogue], ImportResult]:
        """
        Import a single file with automatic format detection.
        
        Args:
            file_path: Path to the file to import
            options: Optional import options (overrides instance options)
            
        Returns:
            Tuple of (Dialogue object or None, ImportResult)
        """
        opts = options or self.options
        
        logger.info(f"Importing file: {file_path}")
        
        # Auto-detect format if needed
        if opts.format == ImportFormat.AUTO:
            detected_format = self._detect_format(file_path)
            logger.debug(f"Auto-detected format: {detected_format}")
        else:
            detected_format = opts.format
        
        # Import based on detected format
        try:
            if detected_format == ImportFormat.DDF:
                return self.ddf_importer.import_file(file_path)
            elif detected_format == ImportFormat.MSG:
                return self.msg_importer.import_file(file_path)
            elif detected_format == ImportFormat.FMF:
                return self._import_fmf(file_path)
            else:
                result = ImportResult(success=False)
                result.add_error(f"Unknown or unsupported format for: {file_path}")
                return None, result
        except Exception as e:
            result = ImportResult(success=False)
            error_msg = log_import_exception(logger, f"importing {file_path}")
            result.add_error(error_msg)
            return None, result
    
    def import_files(self, file_paths: List[Path],
                    transaction_name: str = "batch_import",
                    options: Optional[ImportOptions] = None) -> ImportSummary:
        """
        Import multiple files with transaction support.
        
        Args:
            file_paths: List of paths to import
            transaction_name: Name for the import transaction
            options: Optional import options
            
        Returns:
            ImportSummary with results
        """
        opts = options or self.options
        
        logger.info(f"Starting batch import of {len(file_paths)} files")
        
        result = ImportResult(success=True, total_count=len(file_paths))
        dialogues: List[Dialogue] = []
        
        self.progress.update(0, len(file_paths), "", "Starting batch import")
        
        for i, file_path in enumerate(file_paths):
            self.progress.update(i, len(file_paths), str(file_path), "Importing")
            
            dialogue, file_result = self.import_file(file_path, opts)
            
            if dialogue and file_result.success:
                dialogues.append(dialogue)
                result.imported_count += 1
            else:
                result.skipped_count += 1
                if file_result:
                    result.errors.extend(file_result.errors)
                    result.warnings.extend(file_result.warnings)
                    
                    if not file_result.is_recoverable:
                        logger.warning(f"Non-recoverable error in {file_path}, continuing with next file")
        
        self.progress.update(len(file_paths), len(file_paths), "", "Import complete")
        
        # Update result totals
        result.total_count = len(file_paths)
        result.success = result.errors == []
        
        return ImportSummary(
            total_files=len(file_paths),
            successful=result.imported_count,
            failed=result.skipped_count,
            warnings=len(result.warnings),
            errors=len(result.errors),
            dialogues=dialogues,
            result=result
        )
    
    def import_directory(self, directory: Path,
                        pattern: str = "*",
                        recursive: bool = True,
                        options: Optional[ImportOptions] = None) -> ImportSummary:
        """
        Import all supported files from a directory.
        
        Args:
            directory: Directory to import from
            pattern: File pattern to match (e.g., "*.ddf")
            recursive: Whether to search subdirectories
            options: Optional import options
            
        Returns:
            ImportSummary with results
        """
        logger.info(f"Scanning directory: {directory}")
        
        # Collect all supported files
        file_paths: List[Path] = []
        
        for format_type, extensions in self.FORMAT_EXTENSIONS.items():
            for ext in extensions:
                glob_pattern = f"**/{pattern}{ext}" if recursive else f"{pattern}{ext}"
                file_paths.extend(directory.glob(glob_pattern))
        
        # Remove duplicates (in case multiple extensions match)
        file_paths = list(set(file_paths))
        file_paths.sort()
        
        logger.info(f"Found {len(file_paths)} files to import")
        
        return self.import_files(file_paths, options=options)
    
    def _detect_format(self, file_path: Path) -> ImportFormat:
        """Auto-detect file format based on extension and content"""
        ext = file_path.suffix.lower()
        
        # Check extension first
        for format_type, extensions in self.FORMAT_EXTENSIONS.items():
            if ext in extensions:
                # For MSG files, try to detect if it's Fallout 2 format
                if format_type == ImportFormat.MSG:
                    return self._detect_msg_format(file_path)
                return format_type
        
        # Try to detect by reading file content
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            content_lower = content.lower()
            
            if 'msgoutputname' in content_lower or 'scroputname' in content_lower:
                return ImportFormat.DDF
            if '{' in content and '}' in content:
                # Likely MSG format
                return ImportFormat.MSG
            if 'node ' in content_lower or 'startnodes' in content_lower:
                return ImportFormat.DDF
        except Exception:
            pass
        
        # Default to DDF for unknown files
        logger.warning(f"Could not auto-detect format for {file_path}, defaulting to DDF")
        return ImportFormat.DDF
    
    def _detect_msg_format(self, file_path: Path) -> ImportFormat:
        """Detect MSG format variant"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore', size=1024)
            
            # Check for Fallout 2 extended format markers
            # Fallout 2 has {id}{speaker}{type}... format
            if re.search(r'\{\d+\}\{(\d+)\}\{(\d+)\}', content):
                return ImportFormat.MSG
            
        except Exception:
            pass
        
        return ImportFormat.MSG
    
    def _import_fmf(self, file_path: Path) -> Tuple[Optional[Dialogue], ImportResult]:
        """Import FMF format (legacy)"""
        # Import FMF parser dynamically to avoid circular imports
        try:
            from core.fmf_parser import FMFParser
            
            result = ImportResult(success=False)
            parser = FMFParser()
            
            # Connect to progress
            parser.progress_updated.connect(
                lambda pct, op: self.progress.update(pct, 100, str(file_path), op)
            )
            
            dialogue = parser.parse_file(file_path)
            
            if dialogue:
                result.success = True
                result.imported_count = 1
                return dialogue, result
            else:
                result.add_error(f"Failed to parse FMF file: {file_path}")
                return None, result
                
        except ImportError as e:
            result = ImportResult(success=False)
            result.add_error(f"FMF parser not available: {e}")
            return None, result
        except Exception as e:
            result = ImportResult(success=False)
            error_msg = log_import_exception(logger, f"importing FMF {file_path}")
            result.add_error(error_msg)
            return None, result
    
    def create_import_transaction(self, name: str = "import") -> ImportTransaction:
        """Create a new import transaction"""
        return ImportTransaction(name)
    
    def subscribe_progress(self, callback: Callable[[ImportProgress], None]):
        """Subscribe to progress updates"""
        self.progress.subscribe(callback)
    
    def unsubscribe_progress(self, callback: Callable[[ImportProgress], None]):
        """Unsubscribe from progress updates"""
        self.progress.unsubscribe(callback)


# Import convenience functions

def import_dialogue_file(file_path: Path, 
                         format: ImportFormat = ImportFormat.AUTO,
                         **kwargs) -> Tuple[Optional[Dialogue], ImportResult]:
    """
    Convenience function to import a single dialogue file.
    
    Args:
        file_path: Path to the file
        format: Format of the file (auto-detect by default)
        **kwargs: Additional import options
        
    Returns:
        Tuple of (Dialogue or None, ImportResult)
    """
    options = ImportOptions(format=format, **kwargs)
    manager = ImportManager(options)
    return manager.import_file(file_path)


def import_dialogue_files(file_paths: List[Path],
                          **kwargs) -> ImportSummary:
    """
    Convenience function to import multiple dialogue files.
    
    Args:
        file_paths: List of paths to import
        **kwargs: Additional import options
        
    Returns:
        ImportSummary with results
    """
    options = ImportOptions(**kwargs)
    manager = ImportManager(options)
    return manager.import_files(file_paths)


def import_from_directory(directory: Path,
                         pattern: str = "*",
                         recursive: bool = True,
                         **kwargs) -> ImportSummary:
    """
    Convenience function to import all dialogue files from a directory.
    
    Args:
        directory: Directory to import from
        pattern: File pattern to match
        recursive: Whether to search subdirectories
        **kwargs: Additional import options
        
    Returns:
        ImportSummary with results
    """
    options = ImportOptions(**kwargs)
    manager = ImportManager(options)
    return manager.import_directory(directory, pattern, recursive)


import re
