"""
MSG (Message) Importer for Fallout Dialogue Creator

Provides functionality to import MSG message files into dialogue data.
Supports parsing of Fallout 1/2 MSG format with validation and error handling.

MSG Format:
{ID}{Speaker}{Message}
or
{ID}{Speaker}{MaleText}{FemaleText}

Speaker types:
- 0: NPC
- 1: Player
- 2: System
- 3: Description

Also supports Fallout 2 extended format with additional metadata.
"""

import re
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from models.dialogue import (
    Dialogue, DialogueNode, FloatNode, FloatMessage, FloatMessageType
)
from core.import_base import (
    ImportResult, ImportProgress, ImportProgressReporter,
    ImportValidator, ImportIssue, ImportLevel, log_import_exception
)

logger = logging.getLogger(__name__)


class SpeakerType(Enum):
    """Speaker type codes for MSG files"""
    NPC = 0
    PLAYER = 1
    SYSTEM = 2
    DESCRIPTION = 3
    GM = 4  # Game master messages
    INVALID = -1
    
    @classmethod
    def from_value(cls, value: int) -> 'SpeakerType':
        """Get speaker type from integer value"""
        try:
            return cls(value)
        except ValueError:
            return cls.INVALID
    
    @classmethod
    def from_value_or_str(cls, value) -> 'SpeakerType':
        """Get speaker type from int or string value"""
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            try:
                return cls(int(value))
            except (ValueError, TypeError):
                return cls.INVALID
        if isinstance(value, int):
            try:
                return cls(value)
            except ValueError:
                return cls.INVALID
        return cls.INVALID


@dataclass
class MSGEntry:
    """Represents a single MSG entry"""
    message_id: int
    speaker: SpeakerType = SpeakerType.NPC
    male_text: str = ""
    female_text: str = ""
    line_number: int = 0  # Original line number in file
    
    def is_valid(self) -> bool:
        """Check if entry has valid data"""
        return self.message_id >= 0 and (self.male_text or self.female_text)


class MSGImportValidator(ImportValidator):
    """Validator for MSG import"""
    
    def __init__(self):
        super().__init__()
        self.seen_ids: Dict[int, int] = {}  # Track message IDs to detect duplicates
    
    def validate_entry(self, entry: MSGEntry) -> bool:
        """Validate a single MSG entry"""
        is_valid = True
        
        # Check for duplicate IDs
        if entry.message_id in self.seen_ids:
            self.add_validation_warning(
                f"Duplicate message ID {entry.message_id} (first seen on line {self.seen_ids[entry.message_id]})",
                line_number=entry.line_number
            )
        else:
            self.seen_ids[entry.message_id] = entry.line_number
        
        # Check for empty text
        if not entry.male_text and not entry.female_text:
            self.add_validation_warning(
                f"Message ID {entry.message_id} has no text",
                line_number=entry.line_number
            )
            is_valid = False
        
        # Check for valid speaker type
        speaker_type = SpeakerType.from_value_or_str(entry.speaker)
        if speaker_type == SpeakerType.INVALID:
            self.add_validation_warning(
                f"Message ID {entry.message_id} has invalid speaker type",
                line_number=entry.line_number
            )
        
        return is_valid
    
    def validate_dialogue(self, dialogue: Dialogue) -> bool:
        """Validate the generated dialogue"""
        self.clear()
        
        # Check that we have some content
        if dialogue.nodecount == 0 and dialogue.floatnodecount == 0:
            self.add_validation_warning("No dialogue nodes generated from MSG file")
        
        return True


class MSGImporter:
    """Importer for MSG format files"""
    
    # Regular expressions for parsing MSG
    # Format: {ID}{Speaker}{Message} or {ID}{Speaker}{Male}{Female}
    RE_MSG_ENTRY = re.compile(r'\{(\d+)\}\{(-?\d+)\}\{(.*?)\}(?:\{(.*?)\})?\}', re.DOTALL)
    RE_MSG_ENTRY_WITH_COMMENTS = re.compile(r'\{(\d+)\}\{(-?\d+)\}\{(.*?)\}(?:\{(.*?)\})?\}\s*(?://.*)?$')
    RE_COMMENT_LINE = re.compile(r'^#.*$')
    RE_EMPTY_LINE = re.compile(r'^\s*$')
    
    # Fallout 2 extended format patterns
    RE_FALLOUT2_HEADER = re.compile(r'\{(\d+)\}\{(\d+)\}\{(\d+)\}', re.DOTALL)
    
    def __init__(self, encoding: str = 'cp1252'):
        self.encoding = encoding
        self.validator = MSGImportValidator()
        self.progress = ImportProgressReporter()
        self._entries: List[MSGEntry] = []
        self._npc_name: str = ""
        self._description_nodes: Dict[int, str] = {}
        self._dialogue_nodes: Dict[int, Tuple[str, str]] = {}  # id -> (male, female)
        self._player_responses: Dict[int, str] = {}
    
    def import_file(self, file_path: Path) -> Tuple[Optional[Dialogue], ImportResult]:
        """
        Import an MSG file.
        
        Args:
            file_path: Path to the MSG file
            
        Returns:
            Tuple of (Dialogue object or None, ImportResult)
        """
        result = ImportResult(success=False)
        
        logger.info(f"Starting MSG import from: {file_path}")
        
        try:
            # Validate file exists
            if not file_path.exists():
                result.add_error(f"File not found: {file_path}")
                return None, result
            
            # Detect encoding and read file
            content = self._read_file(file_path)
            if content is None:
                result.add_error(f"Failed to read file: {file_path}")
                return None, result
            
            # Parse content
            entries = self._parse_content(content, result)
            if not entries:
                result.add_error("No valid MSG entries found in file")
                # Return dialogue with defaults instead of None
                dialogue = Dialogue()
                dialogue.filename = file_path.stem
                dialogue.npcname = file_path.stem
                dialogue.unknowndesc = f"You see {file_path.stem}."
                dialogue.knowndesc = dialogue.unknowndesc
                dialogue.detaileddesc = dialogue.unknowndesc
                return dialogue, result
            
            # Convert entries to dialogue
            dialogue = self._entries_to_dialogue(entries, result, file_path)
            if dialogue is None:
                return None, result
            
            # Validate
            if not self.validator.validate_dialogue(dialogue):
                for warning in self.validator.warnings:
                    result.add_warning(warning.message, warning.line_number)
            
            result.success = True
            result.imported_count = dialogue.nodecount + dialogue.floatnodecount
            
            logger.info(f"MSG import completed: {dialogue.nodecount} nodes, {dialogue.floatnodecount} float nodes")
            return dialogue, result
            
        except Exception as e:
            error_msg = log_import_exception(logger, f"importing MSG file {file_path}")
            result.add_error(error_msg)
            return None, result
    
    def import_multiple(self, file_paths: List[Path],
                       transaction_name: str = "msg_import") -> Tuple[List[Dialogue], ImportResult]:
        """
        Import multiple MSG files with transaction support.
        
        Args:
            file_paths: List of paths to MSG files
            transaction_name: Name for the transaction
            
        Returns:
            Tuple of (list of Dialogue objects, ImportResult)
        """
        from core.import_base import ImportTransaction
        
        result = ImportResult(success=True, total_count=len(file_paths))
        dialogues: List[Dialogue] = []
        
        self.progress.update(0, len(file_paths), "", "Starting batch import")
        
        for i, file_path in enumerate(file_paths):
            self.progress.update(i, len(file_paths), str(file_path), "Importing")
            
            dialogue, file_result = self.import_file(file_path)
            
            if dialogue:
                dialogues.append(dialogue)
                result.imported_count += 1
            else:
                result.skipped_count += 1
                result.errors.extend(file_result.errors)
                result.warnings.extend(file_result.warnings)
                
                if not file_result.is_recoverable:
                    result.success = False
                    break
        
        self.progress.update(len(file_paths), len(file_paths), "", "Import complete")
        
        result.total_count = len(file_paths)
        return dialogues, result
    
    def _read_file(self, file_path: Path) -> Optional[str]:
        """Read file with encoding detection"""
        # Try CP1252 first (Fallout 2 default)
        for encoding in [self.encoding, 'cp1252', 'utf-8', 'utf-8-sig', 'iso-8859-1']:
            try:
                content = file_path.read_text(encoding=encoding)
                # Check if we got valid content (contains message markers)
                if '{' in content:
                    logger.debug(f"Successfully read {file_path} with encoding {encoding}")
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.debug(f"Error reading with {encoding}: {e}")
                continue
        
        # Last resort: read as binary and decode with replacement
        try:
            raw_data = file_path.read_bytes()
            return raw_data.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return None
    
    def _parse_content(self, content: str, result: ImportResult) -> List[MSGEntry]:
        """Parse MSG content into entries"""
        entries: List[MSGEntry] = []
        lines = content.split('\n')
        
        # Pre-process: handle line continuations
        processed_lines = []
        current_line = ""
        
        for line in lines:
            line = line.strip()
            
            # Skip pure comment lines
            if self.RE_COMMENT_LINE.match(line):
                continue
            
            # Handle line continuations (lines ending with \)
            if line.endswith('\\'):
                current_line += line[:-1]
                continue
            else:
                current_line += line
            
            if current_line:
                processed_lines.append(current_line)
                current_line = ""
        
        # Don't forget last line if it doesn't end with continuation
        if current_line:
            processed_lines.append(current_line)
        
        total_lines = len(processed_lines)
        
        for line_num, line in enumerate(processed_lines):
            # Update progress
            if line_num % 100 == 0:
                self.progress.update(line_num, total_lines, "", "Parsing MSG entries")
            
            # Skip empty lines
            if not line or self.RE_EMPTY_LINE.match(line):
                continue
            
            # Try to parse the line as MSG entry
            entry = self._parse_line(line, line_num + 1)
            if entry:
                # Validate entry
                self.validator.validate_entry(entry)
                entries.append(entry)
            else:
                # Try more lenient parsing
                entry = self._parse_line_lenient(line, line_num + 1)
                if entry:
                    self.validator.validate_entry(entry)
                    entries.append(entry)
                else:
                    result.add_warning(
                        f"Could not parse line as MSG entry: {line[:50]}...",
                        line_number=line_num + 1
                    )
        
        # Add any validation warnings to result
        for warning in self.validator.warnings:
            result.add_warning(warning.message, warning.line_number)
        
        return entries
    
    def _parse_line(self, line: str, line_number: int) -> Optional[MSGEntry]:
        """Parse a single MSG line"""
        match = self.RE_MSG_ENTRY.match(line)
        
        if not match:
            return None
        
        try:
            message_id = int(match.group(1))
            speaker_value = int(match.group(2))
            male_text = self._decode_message_text(match.group(3))
            female_text = ""
            
            # Check if there's female text
            if match.group(4):
                female_text = self._decode_message_text(match.group(4))
            elif male_text and speaker_value == 3:  # Description type may have implicit female
                female_text = male_text
            
            return MSGEntry(
                message_id=message_id,
                speaker=SpeakerType.from_value(speaker_value),
                male_text=male_text,
                female_text=female_text,
                line_number=line_number
            )
        except (ValueError, IndexError) as e:
            logger.debug(f"Error parsing MSG entry at line {line_number}: {e}")
            return None
    
    def _parse_line_lenient(self, line: str, line_number: int) -> Optional[MSGEntry]:
        """More lenient parsing for malformed MSG entries"""
        # Try to find message ID pattern
        id_match = re.search(r'\{(\d+)\}', line)
        if not id_match:
            return None
        
        try:
            message_id = int(id_match.group(1))
            
            # Try to find speaker
            speaker_match = re.search(r'\}\{(\-?\d+)\}', line)
            speaker_value = int(speaker_match.group(1)) if speaker_match else 0
            
            # Extract text between last { and }
            last_brace_content = re.findall(r'\{([^{}]+)\}', line)
            text_parts = last_brace_content[2:] if len(last_brace_content) > 2 else last_brace_content
            
            male_text = ""
            female_text = ""
            
            if text_parts:
                male_text = self._decode_message_text(text_parts[0])
                if len(text_parts) > 1:
                    female_text = self._decode_message_text(text_parts[1])
            
            return MSGEntry(
                message_id=message_id,
                speaker=SpeakerType.from_value(speaker_value),
                male_text=male_text,
                female_text=female_text,
                line_number=line_number
            )
        except (ValueError, IndexError):
            return None
    
    def _decode_message_text(self, text: str) -> str:
        """Decode MSG message text, handling escape sequences"""
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
    
    def _entries_to_dialogue(self, entries: List[MSGEntry], 
                            result: ImportResult, 
                            file_path: Path) -> Optional[Dialogue]:
        """Convert MSG entries to Dialogue object"""
        dialogue = Dialogue()
        
        # Extract filename for NPC name
        dialogue.filename = file_path.stem
        dialogue.npcname = file_path.stem
        
        # Sort entries by ID
        sorted_entries = sorted(entries, key=lambda e: e.message_id)
        
        # Categorize entries
        description_entries = []
        dialogue_entries = []
        player_entries = []
        system_entries = []
        other_entries = []
        
        for entry in sorted_entries:
            if entry.message_id < 100:
                # Standard description range
                if entry.message_id in (100, 101):  # Look at
                    description_entries.append(entry)
                elif entry.message_id in (102, 103):  # Description
                    description_entries.append(entry)
                else:
                    other_entries.append(entry)
            else:
                # Use helper to handle both string and enum speaker values
                speaker_type = SpeakerType.from_value_or_str(entry.speaker)
                if speaker_type == SpeakerType.NPC:
                    dialogue_entries.append(entry)
                elif speaker_type == SpeakerType.PLAYER:
                    player_entries.append(entry)
                elif speaker_type == SpeakerType.SYSTEM:
                    system_entries.append(entry)
                elif speaker_type == SpeakerType.DESCRIPTION:
                    description_entries.append(entry)
                else:
                    other_entries.append(entry)
        
        # Process description entries
        if description_entries:
            self._process_descriptions(description_entries, dialogue)
        
        # Process dialogue entries as nodes
        if dialogue_entries:
            self._process_dialogue_entries(dialogue_entries, dialogue)
        
        # Process player responses
        if player_entries:
            self._process_player_entries(player_entries, dialogue)
        
        # Process system messages as float nodes
        if system_entries:
            self._process_system_entries(system_entries, dialogue)
        
        # Handle other entries
        if other_entries:
            result.add_warning(
                f"Found {len(other_entries)} entries in non-standard ID range",
            )
            self._process_other_entries(other_entries, dialogue)
        
        # Handle missing descriptions gracefully
        if not dialogue.unknowndesc:
            dialogue.unknowndesc = f"You see {dialogue.npcname}."
        if not dialogue.knowndesc:
            dialogue.knowndesc = dialogue.unknowndesc
        if not dialogue.detaileddesc:
            dialogue.detaileddesc = dialogue.unknowndesc
        
        return dialogue
    
    def _process_descriptions(self, entries: List[MSGEntry], dialogue: Dialogue):
        """Process description entries"""
        for entry in entries:
            if entry.message_id == 100:  # Look at (male)
                if entry.male_text:
                    dialogue.unknowndesc = entry.male_text
            elif entry.message_id == 101:  # Look at (female)
                if entry.female_text or entry.male_text:
                    # Could store separately, but we'll use the first one
                    if not dialogue.unknowndesc:
                        dialogue.unknowndesc = entry.female_text or entry.male_text
            elif entry.message_id == 102:  # Description (male)
                if entry.male_text:
                    dialogue.detaileddesc = entry.male_text
            elif entry.message_id == 103:  # Description (female)
                if entry.female_text or entry.male_text:
                    if not dialogue.detaileddesc:
                        dialogue.detaileddesc = entry.female_text or entry.male_text
    
    def _process_dialogue_entries(self, entries: List[MSGEntry], dialogue: Dialogue):
        """Process dialogue entries as nodes"""
        for entry in entries:
            node = DialogueNode()
            node.nodename = f"node_{entry.message_id}"
            node.npctext = entry.male_text
            node.npctext_female = entry.female_text or entry.male_text
            
            dialogue.nodes.append(node)
            dialogue.nodecount += 1
    
    def _process_player_entries(self, entries: List[MSGEntry], dialogue: Dialogue):
        """Process player response entries"""
        # Player responses typically reference dialogue node IDs
        # We'll create a float node to hold these
        if not dialogue.nodes:
            return
        
        float_node = FloatNode()
        float_node.nodename = "player_responses"
        
        for entry in entries:
            float_node.messages.append(entry.male_text)
            float_node.messagecnt += 1
        
        if float_node.messagecnt > 0:
            dialogue.floatnodes.append(float_node)
            dialogue.floatnodecount += 1
    
    def _process_system_entries(self, entries: List[MSGEntry], dialogue: Dialogue):
        """Process system messages as float nodes"""
        float_node = FloatNode()
        float_node.nodename = "system_messages"
        
        for entry in entries:
            float_node.add_message(entry.male_text, FloatMessageType.SYSTEM_NOTIFICATION)
        
        if float_node.messagecnt > 0:
            dialogue.floatnodes.append(float_node)
            dialogue.floatnodecount += 1
    
    def _process_other_entries(self, entries: List[MSGEntry], dialogue: Dialogue):
        """Process other entries (e.g., 0-99 range not matching standard)"""
        # Create a catch-all float node
        float_node = FloatNode()
        float_node.nodename = "misc_messages"
        
        for entry in entries:
            float_node.add_message(
                f"[{entry.message_id}] {entry.male_text}",
                FloatMessageType.NPC_DIALOGUE
            )
        
        if float_node.messagecnt > 0:
            dialogue.floatnodes.append(float_node)
            dialogue.floatnodecount += 1


class Fallout2MSGImporter(MSGImporter):
    """
    Specialized importer for Fallout 2 MSG format.
    
    Fallout 2 uses a more complex format with additional metadata.
    """
    
    # Fallout 2 extended header format
    RE_FALLOUT2_ENTRY = re.compile(
        r'\{(\d+)\}\{(\d+)\}\{(\d+)\}\{(.*?)\}(?:\{(.*?)\})?(?:\{(.*?)\})?\}',
        re.DOTALL
    )
    
    def _parse_line(self, line: str, line_number: int) -> Optional[MSGEntry]:
        """Parse Fallout 2 extended format line"""
        # Try Fallout 2 format first
        match = self.RE_FALLOUT2_ENTRY.match(line)
        if match:
            try:
                message_id = int(match.group(1))
                speaker_value = int(match.group(2))
                # Group 3 appears to be some type/flags field
                male_text = self._decode_message_text(match.group(4))
                female_text = ""
                
                if match.group(5):
                    female_text = self._decode_message_text(match.group(5))
                
                return MSGEntry(
                    message_id=message_id,
                    speaker=SpeakerType.from_value(speaker_value),
                    male_text=male_text,
                    female_text=female_text,
                    line_number=line_number
                )
            except (ValueError, IndexError):
                pass
        
        # Fall back to standard format
        return super()._parse_line(line, line_number)
