"""
SSL Script Compiler for Fallout Dialogue Creator

Provides Python interface to the SSL (Fallout Scripting Language) compiler
for compiling .ssl scripts to .int format.

Usage:
    compiler = ScriptCompiler()
    result = compiler.compile(Path("myscript.ssl"))
    if result.status == CompileStatus.SUCCESS:
        print(f"Compiled to {result.output_file}")
"""

import subprocess
import logging
import re
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Dict
import shutil
import os
import locale
import platform

logger = logging.getLogger(__name__)

# Default compiler path - can be overridden via environment variable SSL_COMPILER_PATH
# Platform-specific default paths
if platform.system() == "Windows":
    DEFAULT_COMPILER_PATH = Path(os.environ.get('SSL_COMPILER_PATH', 
        r"C:\CodeProjects\sslc_source\Release\sslc.exe"))
elif platform.system() == "Darwin":  # macOS
    DEFAULT_COMPILER_PATH = Path(os.environ.get('SSL_COMPILER_PATH', 
        "/usr/local/bin/sslc"))
else:  # Linux and others
    DEFAULT_COMPILER_PATH = Path(os.environ.get('SSL_COMPILER_PATH', 
        "/usr/local/bin/sslc"))


class CompileStatus(Enum):
    """Status of a compilation result"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    NOT_FOUND = "not_found"


@dataclass
class CompileResult:
    """Result of compiling an SSL script"""
    status: CompileStatus
    input_file: Path
    output_file: Optional[Path] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw_output: str = ""
    
    @property
    def success(self) -> bool:
        """Return True if compilation succeeded"""
        return self.status == CompileStatus.SUCCESS


@dataclass
class HeaderDefinition:
    """Represents a parsed header definition (constant or function)"""
    name: str
    value: str
    is_function: bool = False
    line_number: int = 0
    source_file: Optional[Path] = None


class HeaderPreprocessor:
    """
    Preprocessor for SSL header files.
    
    Parses header files (.h) containing constants and helper functions
    that were originally processed with Watcom C Compiler.
    Supports:
    - #define constants
    - Macro definitions with ## concatenation
    - Helper procedure declarations
    - #include directives (recursive processing)
    """
    
    # Pattern for #define constants: #define NAME value
    DEFINE_PATTERN = re.compile(
        r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+)$',
        re.MULTILINE
    )
    
    # Pattern for #include: #include "filename.h" or #include <filename>
    INCLUDE_PATTERN = re.compile(
        r'^\s*#include\s+["<]([^" >]+)[">]$',
        re.MULTILINE
    )
    
    # Pattern for procedure/function definitions in headers
    PROCEDURE_PATTERN = re.compile(
        r'^\s*(?:procedure|void|int|float)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(',
        re.MULTILINE
    )
    
    def __init__(self, header_paths: Optional[List[Path]] = None):
        """
        Initialize the header preprocessor.
        
        Args:
            header_paths: List of directories to search for header files.
                         If None, uses default paths relative to SSL files.
        """
        self.header_paths: List[Path] = header_paths or []
        self._parsed_headers: Dict[str, Dict[str, HeaderDefinition]] = {}
        self._include_depth: int = 0
        self._max_include_depth: int = 10  # Prevent infinite recursion
    
    def add_header_path(self, path: Path) -> None:
        """Add a directory to search for header files."""
        path = Path(path)
        if path.exists() and path.is_dir():
            self.header_paths.append(path)
            logger.debug(f"Added header search path: {path}")
    
    def parse_header_file(self, header_file: Path) -> Dict[str, HeaderDefinition]:
        """
        Parse a header file and extract definitions.
        
        Args:
            header_file: Path to the header file (.h)
            
        Returns:
            Dictionary mapping definition names to HeaderDefinition objects
        """
        if not header_file.exists():
            logger.warning(f"Header file not found: {header_file}")
            return {}
        
        logger.debug(f"Parsing header file: {header_file}")
        
        try:
            content = header_file.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Error reading header file {header_file}: {e}")
            return {}
        
        definitions = {}
        
        # Parse #define constants
        for match in self.DEFINE_PATTERN.finditer(content):
            name = match.group(1)
            value = match.group(2).strip()
            # Remove trailing semicolon if present
            if value.endswith(';'):
                value = value[:-1].strip()
            
            line_number = content[:match.start()].count('\n') + 1
            definitions[name] = HeaderDefinition(
                name=name,
                value=value,
                is_function=False,
                line_number=line_number,
                source_file=header_file
            )
            logger.debug(f"  Found define: {name} = {value}")
        
        # Parse procedure declarations (helper functions)
        # These are typically in the form: procedure name(args);
        proc_pattern = re.compile(
            r'^\s*procedure\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*;',
            re.MULTILINE
        )
        for match in proc_pattern.finditer(content):
            name = match.group(1)
            if name not in definitions:
                line_number = content[:match.start()].count('\n') + 1
                definitions[name] = HeaderDefinition(
                    name=name,
                    value=match.group(0),
                    is_function=True,
                    line_number=line_number,
                    source_file=header_file
                )
                logger.debug(f"  Found procedure: {name}")
        
        return definitions
    
    def process_includes(self, ssl_content: str, ssl_file: Path) -> Tuple[str, Dict[str, HeaderDefinition]]:
        """
        Process #include directives in SSL content and merge header definitions.
        
        Args:
            ssl_content: The SSL source content
            ssl_file: The main SSL file (for resolving relative paths)
            
        Returns:
            Tuple of (processed_content, combined_definitions)
        """
        all_definitions: Dict[str, HeaderDefinition] = {}
        processed_lines = []
        
        for line in ssl_content.split('\n'):
            include_match = self.INCLUDE_PATTERN.match(line)
            if include_match:
                header_name = include_match.group(1)
                header_defs = self._find_and_parse_header(header_name, ssl_file)
                all_definitions.update(header_defs)
                # Don't include the #include line in output
                logger.debug(f"Processed include: {header_name}")
                continue
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines), all_definitions
    
    def _find_and_parse_header(self, header_name: str, source_file: Path) -> Dict[str, HeaderDefinition]:
        """
        Find and parse a header file by name.
        
        Searches in:
        1. Same directory as source file
        2. Configured header paths
        3. Common include directories
        
        Args:
            header_name: Name of the header file
            source_file: The SSL file that included it
            
        Returns:
            Dictionary of definitions from the header
        """
        if self._include_depth >= self._max_include_depth:
            logger.warning(f"Max include depth exceeded: {header_name}")
            return {}
        
        self._include_depth += 1
        
        try:
            # Search locations
            search_paths = [
                source_file.parent / header_name,  # Same directory
            ]
            
            # Add configured paths
            for path in self.header_paths:
                search_paths.append(Path(path) / header_name)
            
            # Try to find the header file
            for search_path in search_paths:
                if search_path.exists():
                    logger.debug(f"Found header: {search_path}")
                    # Check if already parsed
                    cache_key = str(search_path.resolve())
                    if cache_key in self._parsed_headers:
                        return self._parsed_headers[cache_key]
                    
                    definitions = self.parse_header_file(search_path)
                    self._parsed_headers[cache_key] = definitions
                    return definitions
            
            logger.warning(f"Header not found: {header_name}")
            return {}
        finally:
            self._include_depth -= 1
    
    def preprocess(self, ssl_content: str, ssl_file: Path) -> str:
        """
        Preprocess SSL content by handling includes and merging header definitions.
        
        Args:
            ssl_content: The SSL source content
            ssl_file: The main SSL file
            
        Returns:
            Preprocessed SSL content ready for compilation
        """
        logger.info(f"Preprocessing {ssl_file.name}...")
        
        # Read file content for processing
        ssl_file = Path(ssl_file)
        if not ssl_file.exists():
            logger.error(f"SSL file not found: {ssl_file}")
            return ssl_content if 'ssl_content' in locals() else ""
        
        ssl_content = ssl_file.read_text(encoding='utf-8', errors='replace')
        processed_content, header_defs = self.process_includes(ssl_content, ssl_file)
        
        if not header_defs:
            logger.debug("No header definitions found")
            return ssl_content if ssl_file.exists() else processed_content
        
        # Build header content to prepend
        header_lines = [
            "/* Preprocessed header definitions */",
            "/* Generated by SSL Header Preprocessor (Watcom-compatible) */",
            ""
        ]
        
        for name, definition in sorted(header_defs.items()):
            if definition.is_function:
                header_lines.append(f"/* Function: {name} */")
                header_lines.append(definition.value)
            else:
                header_lines.append(f"#define {name} {definition.value}")
        
        header_block = '\n'.join(header_lines)
        
        # Combine header with processed content
        result = header_block + '\n\n' + processed_content
        
        logger.debug(f"Preprocessing complete: {len(header_defs)} definitions merged")
        return result
    
    def preprocess_file(self, ssl_file: Path) -> str:
        """
        Preprocess an SSL file by reading it, handling includes, and merging definitions.
        
        Args:
            ssl_file: Path to the SSL source file
            
        Returns:
            Preprocessed SSL content ready for compilation
        """
        if not ssl_file.exists():
            logger.error(f"SSL file not found: {ssl_file}")
            return ""
        
        ssl_content = ssl_file.read_text(encoding='utf-8', errors='replace')
        return self.preprocess(ssl_content, ssl_file)
    
    def clear_cache(self) -> None:
        """Clear the parsed header cache."""
        self._parsed_headers.clear()
        self._include_depth = 0
        logger.debug("Header cache cleared")


class ScriptCompiler:
    """
    Wrapper for the SSL script compiler (sslc.exe)
    
    Provides Python API for compiling Fallout scripting language
    source files to .int format.
    """
    
    def __init__(self, compiler_path: Optional[Path] = None, header_paths: Optional[List[Path]] = None):
        """
        Initialize the script compiler.
        
        Args:
            compiler_path: Path to sslc.exe. If None, uses default path.
            header_paths: List of directories to search for header files.
        """
        self.compiler_path = compiler_path or DEFAULT_COMPILER_PATH
        self.preprocessor = HeaderPreprocessor(header_paths)
        self._verify_compiler()
    
    def _verify_compiler(self) -> None:
        """Verify that the compiler exists"""
        if not self.compiler_path.exists():
            logger.warning(f"SSL compiler not found at {self.compiler_path}")
        else:
            logger.debug(f"SSL compiler found at {self.compiler_path}")
    
    def is_available(self) -> bool:
        """Check if the compiler is available"""
        return self.compiler_path.exists() and shutil.which(str(self.compiler_path)) is not None
    
    def add_header_path(self, path: Path) -> None:
        """Add a directory to search for header files during preprocessing."""
        self.preprocessor.add_header_path(path)
    
    def compile(self, ssl_file: Path, show_warnings: bool = True, preprocess: bool = True) -> CompileResult:
        """
        Compile a single SSL source file to INT format.
        
        Args:
            ssl_file: Path to the .ssl source file
            show_warnings: If True, enable warnings in compilation
            preprocess: If True, run header preprocessing pass first
            
        Returns:
            CompileResult with status and output information
        """
        # Validate input file
        ssl_file = Path(ssl_file)
        if not ssl_file.exists():
            logger.error(f"SSL source file not found: {ssl_file}")
            return CompileResult(
                status=CompileStatus.NOT_FOUND,
                input_file=ssl_file,
                errors=[f"File not found: {ssl_file}"]
            )
        
        # Verify compiler exists
        if not self.is_available():
            logger.error(f"SSL compiler not available at {self.compiler_path}")
            return CompileResult(
                status=CompileStatus.ERROR,
                input_file=ssl_file,
                errors=[f"Compiler not found: {self.compiler_path}"]
            )
        
        # Preprocessing pass
        preprocessed_content = None
        temp_file = None
        original_file = ssl_file
        
        if preprocess:
            logger.info(f"Running header preprocessing pass for {ssl_file.name}")
            preprocessed_content = self.preprocessor.preprocess_file(ssl_file)
            
            # Write preprocessed content to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ssl', delete=False, encoding='utf-8') as tmp:
                tmp.write(preprocessed_content)
                temp_file = Path(tmp.name)
            
            ssl_file = temp_file
            logger.debug(f"Preprocessed file written to: {temp_file}")
        
        # Build command
        cmd = [str(self.compiler_path)]
        if show_warnings:
            cmd.append("-w")
        cmd.append(str(ssl_file))
        
        logger.info(f"Compiling {original_file.name}...")
        logger.debug(f"Command: {' '.join(cmd)}")
        
        # Get system-preferred encoding for compiler output
        output_encoding = locale.getpreferredencoding(False)
        logger.debug(f"Using output encoding: {output_encoding}")
        
        try:
            # Run compiler
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding=output_encoding,
                errors='replace',
                cwd=ssl_file.parent
            )
            
            # Parse output
            compile_result = self._parse_compiler_output(
                original_file, result.stdout, result.stderr, result.returncode
            )
            
            if compile_result.success:
                logger.info(f"Successfully compiled {original_file.name}")
            else:
                logger.error(f"Compilation failed for {original_file.name}")
            
            return compile_result
            
        except Exception as e:
            logger.exception(f"Error running compiler: {e}")
            return CompileResult(
                status=CompileStatus.ERROR,
                input_file=original_file,
                errors=[str(e)]
            )
        finally:
            # Clean up temp file
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
    
    def _parse_compiler_output(
        self, 
        ssl_file: Path, 
        stdout: str, 
        stderr: str, 
        returncode: int
    ) -> CompileResult:
        """
        Parse the compiler output to extract errors and warnings.
        
        Args:
            ssl_file: The input SSL file
            stdout: Standard output from compiler
            stderr: Standard error from compiler
            returncode: Exit code from compiler
            
        Returns:
            CompileResult with parsed information
        """
        # Combine outputs
        combined_output = stdout + "\n" + stderr
        
        errors = []
        warnings = []
        
        # Parse error lines
        # Format varies but typically: "Error: message"
        error_pattern = re.compile(r'(?i)error[:\s]+(.+)', re.IGNORECASE)
        for line in combined_output.split('\n'):
            match = error_pattern.search(line)
            if match:
                errors.append(match.group(1).strip())
            elif 'error' in line.lower() and not line.strip().startswith('//'):
                # Some errors might not have the "Error:" prefix
                errors.append(line.strip())
        
        # Parse warning lines  
        warning_pattern = re.compile(r'(?i)warning[:\s]+(.+)', re.IGNORECASE)
        for line in combined_output.split('\n'):
            match = warning_pattern.search(line)
            if match:
                warnings.append(match.group(1).strip())
        
        # Determine status
        if returncode != 0 or errors:
            status = CompileStatus.ERROR
        elif warnings:
            status = CompileStatus.WARNING
        else:
            status = CompileStatus.SUCCESS
        
        # Find output file
        output_file = None
        int_name = ssl_file.stem + ".int"
        potential_output = ssl_file.parent / int_name
        if potential_output.exists():
            output_file = potential_output
        
        return CompileResult(
            status=status,
            input_file=ssl_file,
            output_file=output_file,
            errors=errors,
            warnings=warnings,
            raw_output=combined_output
        )
    
    def compile_batch(
        self, 
        ssl_files: List[Path], 
        show_warnings: bool = True,
        stop_on_error: bool = False,
        preprocess: bool = True
    ) -> List[CompileResult]:
        """
        Compile multiple SSL source files.
        
        Args:
            ssl_files: List of paths to .ssl source files
            show_warnings: If True, enable warnings in compilation
            stop_on_error: If True, stop on first error
            preprocess: If True, run header preprocessing pass first
            
        Returns:
            List of CompileResult, one for each file
        """
        results = []
        
        for ssl_file in ssl_files:
            result = self.compile(ssl_file, show_warnings, preprocess)
            results.append(result)
            
            if stop_on_error and not result.success:
                logger.warning("Stopping compilation due to error")
                break
        
        # Summary
        success_count = sum(1 for r in results if r.success)
        error_count = sum(1 for r in results if r.status == CompileStatus.ERROR)
        warning_count = sum(1 for r in results if r.status == CompileStatus.WARNING)
        
        logger.info(
            f"Compilation complete: {success_count} succeeded, "
            f"{error_count} errors, {warning_count} warnings"
        )
        
        return results
    
    def find_ssl_files(self, directory: Path) -> List[Path]:
        """
        Find all .ssl files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of paths to .ssl files
        """
        directory = Path(directory)
        if not directory.exists():
            return []
        
        return list(directory.glob("*.ssl"))
    
    def compile_directory(
        self, 
        directory: Path, 
        recursive: bool = False,
        show_warnings: bool = True,
        preprocess: bool = True
    ) -> List[CompileResult]:
        """
        Compile all SSL files in a directory.
        
        Args:
            directory: Directory containing .ssl files
            recursive: If True, search subdirectories
            show_warnings: If True, enable warnings
            preprocess: If True, run header preprocessing pass first
            
        Returns:
            List of CompileResult for each file
        """
        if recursive:
            pattern = "**/*.ssl"
        else:
            pattern = "*.ssl"
        
        ssl_files = list(Path(directory).glob(pattern))
        
        if not ssl_files:
            logger.warning(f"No .ssl files found in {directory}")
            return []
        
        logger.info(f"Found {len(ssl_files)} .ssl files to compile")
        
        return self.compile_batch(ssl_files, show_warnings, preprocess=preprocess)
    
    def get_compiler_info(self) -> dict:
        """
        Get information about the compiler.
        
        Returns:
            Dictionary with compiler details
        """
        info = {
            "path": str(self.compiler_path),
            "available": self.is_available(),
            "version": "Unknown"
        }
        
        if info["available"]:
            try:
                result = subprocess.run(
                    [str(self.compiler_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # First line usually contains version info
                first_line = result.stdout.split('\n')[0] if result.stdout else ""
                info["version"] = first_line.strip()
            except Exception as e:
                logger.warning(f"Could not get compiler info: {e}")
        
        return info


# Convenience function for simple usage
def compile_script(ssl_file: Path, preprocess: bool = True, settings=None) -> CompileResult:
    """
    Compile a single SSL script.
    
    Args:
        ssl_file: Path to the .ssl source file
        preprocess: If True, run header preprocessing pass first
        settings: Optional Settings object. If provided, uses the configured 
                  compiler path from settings.
        
    Returns:
        CompileResult
    """
    compiler_path = None
    
    if settings is not None:
        compiler_path = settings.get_script_compiler_path()
    
    compiler = ScriptCompiler(compiler_path=compiler_path)
    return compiler.compile(ssl_file, preprocess=preprocess)
