"""
MSG (Message) Exporter for Fallout Dialogue Creator

Generates proper Fallout 2 compatible MSG message files with:
- NPC dialogue text entries
- Speaker IDs and response text
- Proper Fallout 2 message file format
- Encoding support for special characters (CP1252 for Fallout 2)
- Fallout 1 and Fallout 2 specific formats

The MSG file format:
{ID}{Speaker}{Message}
- ID: Message number (integer)
- Speaker: Speaker type code (0 = NPC, 1 = player, etc.)
- Message: The actual text content
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from models.dialogue import (
    Dialogue, DialogueNode, PlayerOption, FloatNode
)

logger = logging.getLogger(__name__)


class SpeakerType(Enum):
    """Speaker type codes for MSG files"""
    NPC = 0
    PLAYER = 1
    SYSTEM = 2
    DESCRIPTION = 3


@dataclass
class MsgEntry:
    """Represents a single MSG entry"""
    message_id: int
    speaker: int = 0  # Default to NPC
    male_text: str = ""
    female_text: str = ""
    
    def to_msg_line(self) -> str:
        """Convert to MSG file line format"""
        # Format: {ID}{Speaker}{MaleText}{FemaleText}
        # If female text equals male text, only output once
        male = self._format_text(self.male_text)
        female = self._format_text(self.female_text)
        
        if male == female or not female:
            return f"{{{self.message_id}}}{{{self.speaker}}}{{{male}}}"
        else:
            return f"{{{self.message_id}}}{{{self.speaker}}}{{{male}}}{{{female}}}"
    
    def _format_text(self, text: str) -> str:
        """Format text for MSG file"""
        if not text:
            return ""
        
        # Replace newlines with Fallout-style line breaks
        text = text.replace('\r\n', '\\n')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\n')
        
        # Escape special characters
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        
        return text


class MSGExporter:
    """Main MSG exporter class"""
    
    # Standard message IDs
    LOOK_DESCRIPTIONS_BASE = 100
    STARTING_MSG_ID = 100
    
    # Special MSG IDs
    MSG_LOOK_AT_MALE = 100
    MSG_LOOK_AT_FEMALE = 101
    MSG_DESCRIPTION_MALE = 102
    MSG_DESCRIPTION_FEMALE = 103
    
    def __init__(self, encoding: str = "cp1252"):
        """
        Initialize MSG exporter.
        
        Args:
            encoding: Text encoding (cp1252 for Fallout 2, iso8859-1 for Fallout 1)
        """
        self.encoding = encoding
        self.entries: List[MsgEntry] = []
    
    def export(self, dialogue: Dialogue, output_path: Optional[Path] = None) -> str:
        """
        Export dialogue to MSG format.
        
        Args:
            dialogue: Dialogue object to export
            output_path: Optional output file path
            
        Returns:
            Generated MSG content as string
        """
        logger.info(f"Exporting MSG for dialogue: {dialogue.npcname}")
        
        # Generate MSG entries
        self._generate_entries(dialogue)
        
        # Convert to string
        msg_content = self._format_msg()
        
        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                output_path.write_text(msg_content, encoding=self.encoding)
                logger.info(f"MSG exported to: {output_path}")
            except Exception as e:
                # Try with utf-8 as fallback
                try:
                    output_path.write_text(msg_content, encoding='utf-8')
                    logger.warning(f"MSG exported with UTF-8 encoding: {output_path}")
                except Exception as e2:
                    logger.error(f"Failed to write MSG: {e2}")
        
        return msg_content
    
    def _generate_entries(self, dialogue: Dialogue) -> None:
        """Generate MSG entries from dialogue"""
        
        # Clear previous entries
        self.entries = []
        
        # Add look-at and description entries (standard)
        self._add_standard_entries(dialogue)
        
        # Add dialogue node entries
        self._add_dialogue_entries(dialogue)
        
        # Add float message entries
        self._add_float_messages(dialogue)
    
    def _add_standard_entries(self, dialogue: Dialogue) -> None:
        """Add standard look-at and description entries"""
        
        # Look at male (100)
        male_look = dialogue.unknowndesc or f"You see {dialogue.npcname}."
        self.entries.append(MsgEntry(
            message_id=100,
            speaker=SpeakerType.DESCRIPTION.value,
            male_text=male_look,
            female_text=male_look
        ))
        
        # Look at female (101)
        self.entries.append(MsgEntry(
            message_id=101,
            speaker=SpeakerType.DESCRIPTION.value,
            male_text=male_look,
            female_text=male_look
        ))
        
        # Description male (102)
        male_desc = dialogue.detaileddesc or f"You see {dialogue.npcname}."
        self.entries.append(MsgEntry(
            message_id=102,
            speaker=SpeakerType.DESCRIPTION.value,
            male_text=male_desc,
            female_text=male_desc
        ))
        
        # Description female (103)
        self.entries.append(MsgEntry(
            message_id=103,
            speaker=SpeakerType.DESCRIPTION.value,
            male_text=male_desc,
            female_text=male_desc
        ))
    
    def _add_dialogue_entries(self, dialogue: Dialogue) -> None:
        """Add dialogue node entries"""
        
        msg_id = 104  # Start after standard entries
        
        for node in dialogue.nodes:
            node_text = node.npctext or ""
            node_text_female = node.npctext_female or node_text
            
            if node_text:  # Only add entries with text
                self.entries.append(MsgEntry(
                    message_id=msg_id,
                    speaker=SpeakerType.NPC.value,
                    male_text=node_text,
                    female_text=node_text_female
                ))
                msg_id += 1
        
        # Store the next available ID
        self._next_msg_id = msg_id
    
    def _add_float_messages(self, dialogue: Dialogue) -> None:
        """Add floating message entries"""
        
        if not hasattr(self, '_next_msg_id'):
            self._next_msg_id = 104 + len(dialogue.nodes)
        
        msg_id = self._next_msg_id
        
        for float_node in dialogue.floatnodes:
            for message in float_node.messages:
                if message:
                    self.entries.append(MsgEntry(
                        message_id=msg_id,
                        speaker=SpeakerType.SYSTEM.value,
                        male_text=message,
                        female_text=message
                    ))
                    msg_id += 1
    
    def _format_msg(self) -> str:
        """Format all entries as MSG file content"""
        
        lines = []
        
        # Add header comment
        lines.append("# Generated by Fallout Dialogue Creator")
        lines.append(f"# Total entries: {len(self.entries)}")
        lines.append("")
        
        # Add entries
        for entry in self.entries:
            lines.append(entry.to_msg_line())
        
        return '\n'.join(lines)
    
    def get_msg_id_range(self) -> Tuple[int, int]:
        """Get the range of MSG IDs used"""
        if not self.entries:
            return (0, 0)
        
        ids = [e.message_id for e in self.entries]
        return (min(ids), max(ids))
    
    def get_entry_count(self) -> int:
        """Get total number of entries"""
        return len(self.entries)


class MSGExporterCompat:
    """MSG exporter with Fallout 1 compatibility mode"""
    
    def __init__(self, is_fallout1: bool = False):
        """
        Initialize with specific game version.
        
        Args:
            is_fallout1: If True, use Fallout 1 format and encoding
        """
        self.is_fallout1 = is_fallout1
        self.encoding = "iso8859-1" if is_fallout1 else "cp1252"
        self.exporter = MSGExporter(encoding=self.encoding)
    
    def export(self, dialogue: Dialogue, output_path: Optional[Path] = None) -> str:
        """Export dialogue to MSG format with game-specific settings"""
        
        if self.is_fallout1:
            return self._export_fallout1(dialogue, output_path)
        else:
            return self.exporter.export(dialogue, output_path)
    
    def _export_fallout1(self, dialogue: Dialogue, output_path: Optional[Path]) -> str:
        """Export using Fallout 1 format"""
        
        # Fallout 1 MSG format is similar but with slight differences
        # in the encoding and some special character handling
        
        self.exporter._generate_entries(dialogue)
        
        # Add Fallout 1 specific entries if needed
        msg_content = self.exporter._format_msg()
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(msg_content, encoding=self.encoding)
        
        return msg_content


def export_msg(
    dialogue: Dialogue,
    output_path: Optional[Path] = None,
    encoding: str = "cp1252",
    is_fallout1: bool = False
) -> str:
    """
    Convenience function to export MSG.
    
    Args:
        dialogue: Dialogue to export
        output_path: Output file path
        encoding: Text encoding (cp1252 for Fallout 2, iso8859-1 for Fallout 1)
        is_fallout1: Use Fallout 1 format
        
    Returns:
        Generated MSG content
    """
    if is_fallout1:
        exporter = MSGExporterCompat(is_fallout1=True)
    else:
        exporter = MSGExporter(encoding=encoding)
    
    return exporter.export(dialogue, output_path)


def create_msg_filename(dialogue: Dialogue, suffix: str = "") -> str:
    """
    Create appropriate MSG filename from dialogue.
    
    Args:
        dialogue: Dialogue object
        suffix: Optional suffix to add (e.g., "_f" for female variant)
        
    Returns:
        Proper MSG filename
    """
    # Use NPC name, lowercase, replace spaces with underscores
    name = dialogue.npcname.lower().replace(' ', '_').replace('-', '_')
    
    # Remove any invalid filename characters
    name = ''.join(c for c in name if c.isalnum() or c == '_')
    
    return f"{name}{suffix}.msg"


class MSGParser:
    """Parser for existing MSG files"""
    
    # MSG entry pattern: {ID}{Speaker}{Text} or {ID}{Speaker}{Male}{Female}
    ENTRY_PATTERN = r'\{(\d+)\}\{(\d+)\}\{(.*?)\}(?:\{(.*?)\})?\}'
    
    def __init__(self, encoding: str = "cp1252"):
        self.encoding = encoding
    
    def parse_file(self, file_path: Path) -> List[MsgEntry]:
        """Parse an MSG file and return entries"""
        
        content = file_path.read_text(encoding=self.encoding, errors='replace')
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> List[MsgEntry]:
        """Parse MSG content string"""
        
        import re
        
        entries = []
        
        for match in re.finditer(self.ENTRY_PATTERN, content, re.DOTALL):
            msg_id = int(match.group(1))
            speaker = int(match.group(2))
            male_text = match.group(3)
            female_text = match.group(4) if match.group(4) else male_text
            
            # Unescape text
            male_text = male_text.replace('\\{', '{').replace('\\}', '}')
            female_text = female_text.replace('\\{', '{').replace('\\}', '}')
            
            entries.append(MsgEntry(
                message_id=msg_id,
                speaker=speaker,
                male_text=male_text,
                female_text=female_text
            ))
        
        return entries
