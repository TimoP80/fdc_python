"""
Fallout 2 MSG Parser

Provides parsing for Fallout 2 message files using the legacy three-field format:
{id}{audiofile}{message}

Where:
- id: numeric message identifier (required)
- audiofile: optional sound file reference, can be empty (required placeholder)
- message: text content (required)

This parser validates that each line contains exactly three components and rejects
four-field or alternative formats as incompatible with Fallout 2 standards.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Fallout2MsgEntry:
    """Represents a single Fallout 2 MSG entry in three-field format"""
    message_id: int
    audiofile: str
    message: str
    line_number: int = 0
    
    def is_valid(self) -> bool:
        """Check if entry has valid data"""
        return self.message_id >= 0 and self.message is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary for structured output"""
        return {
            'message_id': self.message_id,
            'audiofile': self.audiofile,
            'message': self.message,
            'line_number': self.line_number
        }


@dataclass
class Fallout2MsgParseResult:
    """Result of parsing a Fallout 2 MSG file"""
    entries: List['Fallout2MsgEntry'] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    total_lines: int = 0
    parsed_lines: int = 0
    
    @property
    def is_success(self) -> bool:
        """Check if parsing was successful (no critical errors)"""
        return len(self.errors) == 0 and len(self.entries) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for structured output"""
        return {
            'success': self.is_success,
            'total_lines': self.total_lines,
            'parsed_lines': self.parsed_lines,
            'entries': [e.to_dict() for e in self.entries],
            'errors': self.errors,
            'warnings': self.warnings
        }


class Fallout2FormatError(Exception):
    """Exception raised when a line doesn't match the Fallout 2 three-field format"""
    def __init__(self, message: str, line_number: int = 0, line_content: str = ""):
        self.line_number = line_number
        self.line_content = line_content
        super().__init__(message)


class Fallout2MsgParser:
    """
    Parser for Fallout 2 MSG files using the three-field format.
    
    Format: {id}{audiofile}{message}
    
    This parser:
    - Accepts exactly three fields per line: id, audiofile, message
    - Rejects four-field or alternative formats
    - Handles empty audiofile fields (represented as {})
    - Validates numeric IDs
    - Outputs structured data suitable for further processing
    """
    
    # Regex for exactly three fields: {id}{audiofile}{message}
    # - Field 1: message ID (required, numeric)
    # - Field 2: audiofile (required, can be empty)
    # - Field 3: message text (required)
    RE_THREE_FIELD = re.compile(
        r'^\{(\d+)\}\{(\d*)\}\{(.*)\}$',
        re.DOTALL
    )
    
    # Regex for four fields (should be rejected)
    RE_FOUR_FIELD = re.compile(
        r'^\{(\d+)\}\{(\d*)\}\{(.*)\}\{(.*)\}$',
        re.DOTALL
    )
    
    # Regex for alternate format with speaker type (should be rejected)
    RE_SPEAKER_FORMAT = re.compile(
        r'^\{(\d+)\}\{(\d+)\}\{(.*)\}(?:\{(.*)\})?\}$',
        re.DOTALL
    )
    
    # Pattern for comment lines
    RE_COMMENT = re.compile(r'^\s*#')
    
    # Pattern for empty lines
    RE_EMPTY = re.compile(r'^\s*$')
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize the parser.
        
        Args:
            strict_mode: If True, raises exceptions on format errors.
                        If False, collects errors in result instead.
        """
        self.strict_mode = strict_mode
    
    def parse(self, content: str) -> Fallout2MsgParseResult:
        """
        Parse the entire MSG file content.
        
        Args:
            content: The raw content of the MSG file
            
        Returns:
            Fallout2MsgParseResult with parsed entries and any errors/warnings
        """
        result = Fallout2MsgParseResult()
        lines = content.split('\n')
        result.total_lines = len(lines)
        
        for line_num, line in enumerate(lines, start=1):
            # Skip comments and empty lines
            if self.RE_COMMENT.match(line) or self.RE_EMPTY.match(line):
                continue
            
            # Try to parse the line
            entry = self._parse_line(line, line_num)
            
            if entry is not None:
                result.entries.append(entry)
                result.parsed_lines += 1
            # If entry is None, an error was already logged
        
        return result
    
    def parse_file(self, file_path: Path) -> Fallout2MsgParseResult:
        """
        Parse an MSG file from disk.
        
        Args:
            file_path: Path to the MSG file
            
        Returns:
            Fallout2MsgParseResult with parsed entries and any errors/warnings
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return self.parse(content)
        except FileNotFoundError:
            result = Fallout2MsgParseResult()
            result.errors.append({
                'type': 'file_not_found',
                'message': f'File not found: {file_path}',
                'line_number': 0
            })
            return result
        except Exception as e:
            result = Fallout2MsgParseResult()
            result.errors.append({
                'type': 'read_error',
                'message': str(e),
                'line_number': 0
            })
            return result
    
    def _parse_line(self, line: str, line_number: int) -> Optional[Fallout2MsgEntry]:
        """
        Parse a single MSG line in three-field format.
        
        Args:
            line: The line to parse
            line_number: Line number for error reporting
            
        Returns:
            Fallout2MsgEntry if successful, None if parsing failed
        """
        line = line.strip()
        
        # Skip comments and empty lines
        if self.RE_COMMENT.match(line) or self.RE_EMPTY.match(line):
            return None
        
        # First, check for four-field format (must be rejected)
        four_field_match = self.RE_FOUR_FIELD.match(line)
        if four_field_match:
            error = self._create_error(
                line_number,
                line,
                "Four-field format detected. Fallout 2 standard requires exactly three fields: {id}{audiofile}{message}"
            )
            if self.strict_mode:
                raise Fallout2FormatError(
                    f"Line {line_number}: Four-field format not supported. "
                    f"Expected three fields: {{id}}{{audiofile}}{{message}}",
                    line_number,
                    line
                )
            self._log_error(error)
            return None
        
        # Check for speaker format (must be rejected as alternative format)
        speaker_match = self.RE_SPEAKER_FORMAT.match(line)
        if speaker_match:
            # Check if it has 4 groups (4 fields) vs 3 groups (3 fields with speaker ID 0-4)
            groups = speaker_match.groups()
            if len([g for g in groups if g is not None]) >= 4:
                error = self._create_error(
                    line_number,
                    line,
                    "Alternative format with speaker type detected. This parser requires three-field format: {id}{audiofile}{message}"
                )
                if self.strict_mode:
                    raise Fallout2FormatError(
                        f"Line {line_number}: Speaker format not supported. "
                        f"Use three-field format: {{id}}{{audiofile}}{{message}}",
                        line_number,
                        line
                    )
                self._log_error(error)
                return None
        
        # Now try to match three-field format
        three_field_match = self.RE_THREE_FIELD.match(line)
        
        if not three_field_match:
            error = self._create_error(
                line_number,
                line,
                "Invalid format. Expected: {id}{audiofile}{message}"
            )
            if self.strict_mode:
                raise Fallout2FormatError(
                    f"Line {line_number}: Invalid format. "
                    f"Expected three fields: {{id}}{{audiofile}}{{message}}",
                    line_number,
                    line
                )
            self._log_error(error)
            return None
        
        try:
            message_id = int(three_field_match.group(1))
            audiofile = three_field_match.group(2)  # Can be empty string
            message = self._decode_message(three_field_match.group(3))
            
            # Validate message ID is non-negative
            if message_id < 0:
                error = self._create_warning(
                    line_number,
                    line,
                    f"Negative message ID {message_id} detected"
                )
                logger.warning(error['message'])
            
            # Validate message is not empty
            if not message:
                error = self._create_warning(
                    line_number,
                    line,
                    f"Empty message for ID {message_id}"
                )
                logger.warning(error['message'])
            
            return Fallout2MsgEntry(
                message_id=message_id,
                audiofile=audiofile,
                message=message,
                line_number=line_number
            )
            
        except (ValueError, IndexError) as e:
            error = self._create_error(
                line_number,
                line,
                f"Failed to parse entry: {str(e)}"
            )
            if self.strict_mode:
                raise Fallout2FormatError(
                    f"Line {line_number}: Parse error - {str(e)}",
                    line_number,
                    line
                )
            self._log_error(error)
            return None
    
    def _decode_message(self, text: str) -> str:
        """
        Decode MSG message text, handling escape sequences.
        
        Args:
            text: The raw message text
            
        Returns:
            Decoded message text
        """
        if not text:
            return ""
        
        # Unescape Fallout-style sequences
        text = text.replace('\\n', '\n')
        text = text.replace('\\t', '\t')
        text = text.replace('\\{', '{')
        text = text.replace('\\}', '}')
        text = text.replace('\\\\', '\\')
        
        # Remove any remaining control characters except newlines
        text = re.sub(r'[\x00-\x09\x0b-\x1f]', '', text)
        
        return text.strip()
    
    def _create_error(self, line_number: int, line: str, message: str) -> Dict[str, Any]:
        """Create an error dictionary"""
        return {
            'type': 'parse_error',
            'line_number': line_number,
            'line_content': line,
            'message': message
        }
    
    def _create_warning(self, line_number: int, line: str, message: str) -> Dict[str, Any]:
        """Create a warning dictionary"""
        return {
            'type': 'warning',
            'line_number': line_number,
            'line_content': line,
            'message': message
        }
    
    def _log_error(self, error: Dict[str, Any]):
        """Log error to the parser's error tracking"""
        # This will be handled by the parse result
        pass


class Fallout2MsgParserWithResult(Fallout2MsgParser):
    """Extended parser that tracks errors and warnings in the result"""
    
    def __init__(self, strict_mode: bool = True):
        super().__init__(strict_mode)
        self._errors: List[Dict[str, Any]] = []
        self._warnings: List[Dict[str, Any]] = []
    
    def parse(self, content: str) -> Fallout2MsgParseResult:
        """Parse with error and warning tracking"""
        self._errors = []
        self._warnings = []
        
        result = super().parse(content)
        result.errors = self._errors
        result.warnings = self._warnings
        
        return result
    
    def _log_error(self, error: Dict[str, Any]):
        self._errors.append(error)
    
    def _log_warning(self, warning: Dict[str, Any]):
        self._warnings.append(warning)


def parse_fallout2_msg(content: str, strict: bool = False) -> Fallout2MsgParseResult:
    """
    Convenience function to parse Fallout 2 MSG content.
    
    Args:
        content: Raw MSG file content
        strict: If True, raise exceptions on format errors
        
    Returns:
        Fallout2MsgParseResult with parsed data
    """
    parser = Fallout2MsgParserWithResult(strict_mode=strict)
    return parser.parse(content)


def parse_fallout2_msg_file(file_path: str, strict: bool = False) -> Fallout2MsgParseResult:
    """
    Convenience function to parse a Fallout 2 MSG file.
    
    Args:
        file_path: Path to the MSG file
        strict: If True, raise exceptions on format errors
        
    Returns:
        Fallout2MsgParseResult with parsed data
    """
    parser = Fallout2MsgParserWithResult(strict_mode=strict)
    return parser.parse_file(Path(file_path))
