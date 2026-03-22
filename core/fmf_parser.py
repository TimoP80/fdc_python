"""
FMF file parser for Fallout Dialogue Creator
Based on the original Delphi FMF parser
"""

import re
from typing import TextIO, Optional, List, Dict, Any
from pathlib import Path
import logging
import sys
import gc

from PyQt6.QtCore import QObject, pyqtSignal

from models.dialogue import (
    Dialogue, DialogueNode, PlayerOption, Condition, SkillCheck,
    FloatNode, TimeEvent, Action, Variable, StartingCondition,
    CustomProcedure, Reaction, Gender, CheckType, CompareType, LinkType
)

logger = logging.getLogger(__name__)

# Common encodings to try when loading FMF files
COMMON_ENCODINGS = [
    'utf-8-sig',  # UTF-8 with BOM
    'utf-16',     # UTF-16 (will auto-detect LE/BE)
    'utf-16-le',  # UTF-16 Little Endian
    'utf-16-be',  # UTF-16 Big Endian
    'cp1252',     # Windows-1252 (Western European)
    'iso-8859-1', # Latin-1
    'latin1',     # Latin-1 (alternative name)
    'cp437',      # DOS code page 437
    'cp850',      # DOS code page 850
    'mac_roman',  # Mac Roman
]

# Pre-computed BOM signatures
BOM_UTF8 = b'\xef\xbb\xbf'
BOM_UTF16_LE = b'\xff\xfe'
BOM_UTF16_BE = b'\xfe\xff'
BOM_UTF32_LE = b'\xff\xfe\x00\x00'
BOM_UTF32_BE = b'\x00\x00\xfe\xff'

class FMFParser(QObject):
    """Parser for FMF dialogue files (text format)"""

    # Progress signals
    progress_updated = pyqtSignal(int, str)  # progress percentage, current operation

    def __init__(self):
        super().__init__()
        self.current_dialogue: Optional[Dialogue] = None
        self._last_detected_encoding: Optional[str] = None

    def _detect_encoding(self, file_path: Path) -> str:
        """
        Detect the encoding of an FMF file by checking BOM and trying to decode.
        
        Args:
            file_path: Path to the FMF file
            
        Returns:
            Detected encoding name (can be used with open())
        """
        try:
            # Read the first few bytes to check for BOM
            with open(file_path, 'rb') as f:
                raw_data = f.read(4096)  # Read first 4KB for BOM detection
            
            # Check for UTF-8 BOM
            if raw_data.startswith(BOM_UTF8):
                logger.debug(f"Detected UTF-8 BOM in {file_path}")
                self._last_detected_encoding = 'utf-8-sig'
                return 'utf-8-sig'
            
            # Check for UTF-16 LE BOM
            if raw_data.startswith(BOM_UTF16_LE):
                logger.debug(f"Detected UTF-16 LE BOM in {file_path}")
                self._last_detected_encoding = 'utf-16-le'
                return 'utf-16-le'
            
            # Check for UTF-16 BE BOM
            if raw_data.startswith(BOM_UTF16_BE):
                logger.debug(f"Detected UTF-16 BE BOM in {file_path}")
                self._last_detected_encoding = 'utf-16-be'
                return 'utf-16-be'
            
            # Check for UTF-32 BOMs
            if raw_data.startswith(BOM_UTF32_LE) or raw_data.startswith(BOM_UTF32_BE):
                logger.warning(f"UTF-32 encoding detected in {file_path}, attempting to handle")
                self._last_detected_encoding = 'utf-32'
                return 'utf-32'
            
            # No BOM found, try to detect encoding by attempting decode
            # Start with UTF-8, then try common legacy encodings
            return self._detect_encoding_by_decoding(file_path)
            
        except Exception as e:
            logger.warning(f"Error detecting encoding for {file_path}: {e}, defaulting to utf-8")
            return 'utf-8'

    def _detect_encoding_by_decoding(self, file_path: Path) -> str:
        """
        Try to detect encoding by attempting to decode the file content.
        
        Args:
            file_path: Path to the FMF file
            
        Returns:
            Detected encoding name
        """
        # Try UTF-16 first (before UTF-8) because it has distinct byte patterns
        # that can confuse other decoders
        for encoding in ['utf-16', 'utf-16-le', 'utf-16-be']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # Verify we got valid content
                    if content and len(content.strip()) > 0:
                        logger.debug(f"Detected {encoding} encoding in {file_path}")
                        self._last_detected_encoding = encoding
                        return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Try UTF-8
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
            logger.debug(f"Detected UTF-8 encoding (no BOM) in {file_path}")
            self._last_detected_encoding = 'utf-8'
            return 'utf-8'
        except UnicodeDecodeError:
            pass
        
        # Try each common encoding in order
        for encoding in COMMON_ENCODINGS:
            # Skip UTF-16 variants as we already tried them
            if encoding.startswith('utf-16'):
                continue
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # Verify we got valid content
                    if content and len(content.strip()) > 0:
                        logger.debug(f"Detected {encoding} encoding in {file_path}")
                        self._last_detected_encoding = encoding
                        return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Last resort: use errors='replace' with UTF-8
        logger.warning(f"Could not detect encoding for {file_path}, using UTF-8 with error replacement")
        self._last_detected_encoding = 'utf-8'
        return 'utf-8'

    def _read_file_with_encoding(self, file_path: Path, encoding: str) -> str:
        """
        Read file content with specified encoding, handling errors gracefully.
        
        Args:
            file_path: Path to the FMF file
            encoding: The encoding to use
            
        Returns:
            File content as string
        """
        try:
            # Try strict reading first
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError as e:
            logger.warning(f"Strict decode failed with {encoding}: {e}, trying with error replacement")
            # Fall back to error replacement mode
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file with {encoding}: {e}")
            raise

    def load_from_file(self, file_path: Path) -> Dialogue:
        """Load dialogue from FMF file with automatic encoding detection"""
        try:
            # Detect encoding first
            detected_encoding = self._detect_encoding(file_path)
            logger.info(f"Loading FMF file {file_path} with detected encoding: {detected_encoding}")
            
            # Read with detected encoding
            content = self._read_file_with_encoding(file_path, detected_encoding)
            
            # Create a StringIO-like stream for parse_fmf
            from io import StringIO
            stream = StringIO(content)
            return self.parse_fmf(stream)
        except Exception as e:
            logger.error(f"Failed to load FMF file {file_path}: {e}")
            raise

    def save_to_file(self, dialogue: Dialogue, file_path: Path, encoding: str = 'utf-8') -> None:
        """Save dialogue to FMF file with specified encoding"""
        try:
            with open(file_path, 'w', encoding=encoding, errors='replace') as f:
                self.write_fmf(dialogue, f)
        except Exception as e:
            logger.error(f"Failed to save FMF file {file_path}: {e}")
            raise

    def parse_fmf(self, stream: TextIO) -> Dialogue:
        """Parse FMF format from text stream"""
        dialogue = Dialogue()
        current_line = 0

        try:
            logger.debug("FMF parsing started - reading file content")
            self.progress_updated.emit(10, "Reading file content...")
            content = stream.read()
            current_line = content.count('\n') + 1
            logger.debug(f"FMF parsing: Read {len(content)} characters, {current_line} lines")
            logger.debug(f"FMF parsing: Memory usage before parsing - {sys.getsizeof(content)} bytes for content")
            gc.collect()
            logger.debug(f"FMF parsing: Memory after GC - {sys.getsizeof(content)} bytes for content")

            # Validate basic FMF structure
            if not content.strip():
                raise ValueError("FMF file is empty")

            if '/*' not in content or '*/' not in content:
                logger.warning("FMF file header comment not found")

            # Remove comments
            logger.debug("FMF parsing - processing comments")
            self.progress_updated.emit(20, "Processing comments...")
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            logger.debug(f"FMF parsing: Content after comment removal has {len(content)} characters")

            lines = content.split('\n')
            i = 0
            total_lines = len(lines)
            logger.debug(f"FMF parsing: Split into {total_lines} lines")
            logger.debug(f"FMF parsing: Memory usage after splitting - {sys.getsizeof(lines)} bytes for lines list")
            gc.collect()
            logger.debug(f"FMF parsing: Memory after GC - {sys.getsizeof(lines)} bytes for lines list")

            # Validate we have content after comment removal
            if not any(line.strip() for line in lines):
                raise ValueError("FMF file contains no content after comment removal")

            # Parse global properties
            logger.debug("FMF parsing - parsing global properties")
            self.progress_updated.emit(30, "Parsing global properties...")
            global_props_found = False
            while i < len(lines):
                line = lines[i].strip()
                current_line = i + 1
                if not line or line.startswith('//'):
                    i += 1
                    continue

                try:
                    if line.startswith('NPCName'):
                        dialogue.npcname = self._parse_quoted_string(line)
                        global_props_found = True
                        logger.debug(f"FMF parsing: Found NPCName: {dialogue.npcname}")
                    elif line.startswith('Location'):
                        dialogue.location = self._parse_quoted_string(line)
                        global_props_found = True
                        logger.debug(f"FMF parsing: Found Location: {dialogue.location}")
                    elif line.startswith('Description'):
                        dialogue.description = self._parse_quoted_string(line)
                        global_props_found = True
                        logger.debug(f"FMF parsing: Found Description: {dialogue.description}")
                    elif line.startswith('Unknown_Desc'):
                        dialogue.unknowndesc = self._parse_quoted_string(line)
                        global_props_found = True
                        logger.debug(f"FMF parsing: Found Unknown_Desc: {dialogue.unknowndesc}")
                    elif line.startswith('Known_Desc'):
                        dialogue.knowndesc = self._parse_quoted_string(line)
                        global_props_found = True
                        logger.debug(f"FMF parsing: Found Known_Desc: {dialogue.knowndesc}")
                    elif line.startswith('Detailed_Desc'):
                        dialogue.detaileddesc = self._parse_quoted_string(line)
                        global_props_found = True
                        logger.debug(f"FMF parsing: Found Detailed_Desc: {dialogue.detaileddesc}")
                    elif line.startswith('StartTimeEvent'):
                        # Parse start time event
                        match = re.search(r'StartTimeEvent\s+(\d+)', line)
                        if match:
                            dialogue.start_time_event = int(match.group(1))
                            logger.debug(f"FMF parsing: Found StartTimeEvent: {dialogue.start_time_event}")
                    elif line.startswith('StartCondition'):
                        # Parse starting condition
                        start_cond = self._parse_start_condition(line)
                        if start_cond:
                            dialogue.startconditions.append(start_cond)
                            dialogue.startconditioncnt += 1
                            logger.debug(f"FMF parsing: Found StartCondition with {len(start_cond.conditions)} conditions")
                    elif line.startswith('CustomProc'):
                        # Parse custom procedure
                        proc, new_i = self._parse_custom_proc(lines, i)
                        if proc:
                            dialogue.customprocs.append(proc)
                            dialogue.customproccnt += 1
                            logger.debug(f"FMF parsing: Found CustomProc: {proc.name}")
                        if new_i > i:
                            i = new_i
                    elif line.startswith('TimedEvent'):
                        # Parse timed event
                        timed_event, new_i = self._parse_timed_event(lines, i)
                        if timed_event:
                            dialogue.timedevents.append(timed_event)
                            dialogue.timedeventcnt += 1
                            logger.debug(f"FMF parsing: Found TimedEvent: {timed_event.fixedparamname}")
                        if new_i > i:
                            i = new_i
                    elif line.startswith('Variable'):
                        # Parse variable
                        var = self._parse_variable(line)
                        if var:
                            dialogue.variables.append(var)
                            dialogue.varcnt += 1
                            logger.debug(f"FMF parsing: Found Variable: {var.name}")
                    elif line.startswith('FloatNode '):
                        # Parse float node
                        float_node, new_i = self._parse_float_node(lines, i)
                        if float_node:
                            dialogue.floatnodes.append(float_node)
                            dialogue.floatnodecount += 1
                            logger.debug(f"FMF parsing: Found FloatNode: {float_node.nodename}")
                            i = new_i
                        else:
                            i += 1
                        continue
                    elif line.startswith('Node '):
                        # Start parsing nodes (don't increment i - let node parser handle it)
                        logger.debug(f"FMF parsing: Found first node at line {current_line}, stopping global properties parsing")
                        break
                    else:
                        logger.warning(f"Unknown global property at line {current_line}: {line}")
                except Exception as e:
                    logger.error(f"Error parsing global property at line {current_line}: {line}. Error: {e}")
                    raise ValueError(f"Failed to parse global property at line {current_line}: {e}") from e
                i += 1

            if not global_props_found:
                logger.warning("No global properties found in FMF file")

            # Parse nodes
            logger.debug("FMF parsing - parsing dialogue nodes")
            self.progress_updated.emit(50, "Parsing dialogue nodes...")
            node_count = 0
            loop_iterations = 0
            max_iterations = total_lines * 2  # Safety limit
            while i < len(lines):
                loop_iterations += 1
                if loop_iterations > max_iterations:
                    logger.error(f"FMF parsing: Potential infinite loop detected at line {i+1}, iterations: {loop_iterations}")
                    raise ValueError(f"Parsing exceeded maximum iterations ({max_iterations}) - possible infinite loop")

                line = lines[i].strip()
                current_line = i + 1
                if line.startswith('Node '):
                    try:
                        logger.debug(f"FMF parsing: Parsing node at line {current_line}")
                        node = self._parse_node(lines, i)
                        dialogue.nodes.append(node)
                        dialogue.nodecount += 1
                        node_count += 1
                        logger.debug(f"FMF parsing: Successfully parsed node '{node.nodename}' with {len(node.options)} options")
                        logger.debug(f"FMF parsing: Memory usage after node {node_count} - {sys.getsizeof(dialogue.nodes)} bytes for nodes list")

                        # Update progress for nodes (50-90% range)
                        progress = 50 + int((node_count / max(1, len(dialogue.nodes))) * 40)
                        self.progress_updated.emit(min(progress, 90), f"Parsed {node_count} nodes...")
                        logger.debug(f"FMF parsing: Progress updated to {min(progress, 90)}% after parsing {node_count} nodes")
                    except Exception as e:
                        logger.error(f"Error parsing node at line {current_line}: {line}. Error: {e}")
                        raise ValueError(f"Failed to parse node at line {current_line}: {e}") from e

                i += 1

                # Update progress periodically even if no nodes found yet
                if i % 100 == 0 and node_count == 0:
                    progress = 50 + int((i / max(1, total_lines)) * 40)
                    self.progress_updated.emit(min(progress, 90), f"Scanning for nodes... ({i}/{total_lines})")
                    logger.debug(f"FMF parsing: Periodic progress update to {min(progress, 90)}% at line {i}/{total_lines}")

            logger.debug("FMF parsing - finalizing dialogue")
            self.progress_updated.emit(95, "Finalizing dialogue...")
            logger.debug(f"FMF parsing: Finalizing dialogue with {len(dialogue.nodes)} nodes")

            # Validate parsed dialogue
            if not dialogue.nodes:
                logger.warning("No nodes found in FMF file")
            else:
                logger.info(f"Successfully parsed {len(dialogue.nodes)} nodes")

            if not dialogue.npcname:
                logger.warning("No NPC name found in FMF file")

            # Check for basic structural integrity
            for idx, node in enumerate(dialogue.nodes):
                if not node.nodename:
                    logger.warning(f"Node {idx} has no name")
                if not node.npctext and not node.options:
                    logger.warning(f"Node '{node.nodename}' has no NPC text and no options")

            logger.debug("FMF parsing completed successfully")
            self.progress_updated.emit(100, "Parsing complete")
            logger.debug("FMF parsing: Emitted 100% progress - parsing complete")
            return dialogue

        except Exception as e:
            logger.error(f"Critical parsing error at line {current_line}: {e}")
            raise ValueError(f"FMF parsing failed at line {current_line}: {e}") from e

    def _parse_quoted_string(self, line: str) -> str:
        """Parse a quoted string from a line like 'Property "value"'"""
        match = re.search(r'"([^"]*)"', line)
        if match:
            return match.group(1)
        else:
            logger.warning(f"Could not parse quoted string from line: {line}")
            return ""

    def _parse_node(self, lines: List[str], start_idx: int) -> DialogueNode:
        """Parse a single node from the FMF content"""
        node = DialogueNode()
        i = start_idx
        current_line = start_idx + 1
        loop_iterations = 0
        max_iterations = len(lines) - start_idx + 100  # Safety limit

        try:
            # Parse node name
            line = lines[i].strip()
            match = re.search(r'Node\s+"([^"]*)"', line)
            if match:
                node.nodename = match.group(1)
            else:
                logger.warning(f"Could not parse node name at line {current_line}: {line}")

            i += 1
            current_line += 1

            # Parse node properties
            while i < len(lines):
                loop_iterations += 1
                if loop_iterations > max_iterations:
                    logger.error(f"FMF parsing: Potential infinite loop in node properties at line {current_line}, iterations: {loop_iterations}")
                    raise ValueError(f"Node parsing exceeded maximum iterations ({max_iterations}) - possible infinite loop")

                line = lines[i].strip()
                current_line = i + 1

                if line.startswith('notes'):
                    node.notes = self._parse_quoted_string(line)
                elif line.startswith('is_wtg'):
                    try:
                        node.is_wtg = line.split('=')[1].strip().lower() == 'true'
                    except IndexError:
                        logger.warning(f"Invalid is_wtg format at line {current_line}: {line}")
                        node.is_wtg = False
                elif line == '{':
                    # Start of node content
                    i += 1
                    current_line += 1
                    break
                elif line.startswith('Node ') or not line:
                    # Next node or empty line, stop parsing this node
                    break
                else:
                    logger.warning(f"Unknown node property at line {current_line}: {line}")
                i += 1

            # Parse node content
            content_iterations = 0
            while i < len(lines):
                content_iterations += 1
                if content_iterations > max_iterations:
                    logger.error(f"FMF parsing: Potential infinite loop in node content at line {current_line}, iterations: {content_iterations}")
                    raise ValueError(f"Node content parsing exceeded maximum iterations ({max_iterations}) - possible infinite loop")

                line = lines[i].strip()
                current_line = i + 1

                if line.startswith('NPCText'):
                    node.npctext = self._parse_quoted_string(line)
                elif line.startswith('NPCFEMALETEXT'):
                    node.npctext_female = self._parse_quoted_string(line)
                elif line.startswith('options'):
                    try:
                        i = self._parse_options(lines, i, node)
                        current_line = i + 1
                    except Exception as e:
                        logger.error(f"Error parsing options at line {current_line}: {e}")
                        raise ValueError(f"Failed to parse options at line {current_line}: {e}") from e
                elif line == '}':
                    # End of node
                    break
                elif line.startswith('Node ') or not line:
                    # Next node or empty line, stop parsing this node
                    break
                else:
                    logger.warning(f"Unknown node content at line {current_line}: {line}")
                i += 1

            # Validate node
            if not node.nodename:
                logger.warning(f"Node at line {start_idx + 1} has no name")

            return node

        except Exception as e:
            logger.error(f"Error parsing node at line {current_line}: {e}")
            raise ValueError(f"Failed to parse node at line {current_line}: {e}") from e

    def _parse_options(self, lines: List[str], start_idx: int, node: DialogueNode) -> int:
        """Parse options block, returns new index"""
        i = start_idx
        current_line = start_idx + 1
        loop_iterations = 0
        max_iterations = len(lines) - start_idx + 100  # Safety limit

        try:
            # Skip 'options {' line
            while i < len(lines) and '{' not in lines[i]:
                i += 1
                current_line += 1
            if i >= len(lines):
                logger.warning(f"Options block not properly opened at line {current_line}")
                return i
            i += 1
            current_line += 1

            while i < len(lines):
                loop_iterations += 1
                if loop_iterations > max_iterations:
                    logger.error(f"FMF parsing: Potential infinite loop in options parsing at line {current_line}, iterations: {loop_iterations}")
                    raise ValueError(f"Options parsing exceeded maximum iterations ({max_iterations}) - possible infinite loop")

                line = lines[i].strip()
                current_line = i + 1

                if line == '}':
                    # End of options
                    break

                if line.startswith('int='):
                    try:
                        option = self._parse_option(lines, i)
                        node.options.append(option)
                        node.optioncnt += 1
                        logger.debug(f"FMF parsing: Parsed option {node.optioncnt} for node '{node.nodename}'")

                        # Move to the next line after parsing this option
                        i += 1
                        current_line += 1
                        continue
                    except Exception as e:
                        logger.error(f"Error parsing option at line {current_line}: {e}")
                        # Continue parsing other options instead of failing completely
                        # Move to the next line after the failed option
                        i += 1
                        current_line += 1
                        continue
                elif line and not line.startswith('//'):
                    logger.warning(f"Unexpected line in options block at line {current_line}: {line}")

                i += 1

            return i

        except Exception as e:
            logger.error(f"Error parsing options block at line {current_line}: {e}")
            raise ValueError(f"Failed to parse options block at line {current_line}: {e}") from e

    def _parse_option(self, lines: List[str], start_idx: int) -> PlayerOption:
        """Parse a single option"""
        i = start_idx
        current_line = start_idx + 1

        try:
            # Parse the single line with all option data
            line = lines[i].strip()

            # Extract int value
            intcheck = 4  # default
            match = re.search(r'int=(\d+)', line)
            if match:
                try:
                    intcheck = int(match.group(1))
                except ValueError:
                    logger.warning(f"Invalid int value at line {current_line}: {match.group(1)}")
                    intcheck = 4

            # Extract reaction
            reaction = Reaction.NEUTRAL  # default
            match = re.search(r'Reaction=REACTION_(\w+)', line)
            if match:
                reaction_name = match.group(1)
                if reaction_name == 'NEUTRAL':
                    reaction = Reaction.NEUTRAL
                elif reaction_name == 'GOOD':
                    reaction = Reaction.GOOD
                elif reaction_name == 'BAD':
                    reaction = Reaction.BAD
                else:
                    logger.warning(f"Unknown reaction type at line {current_line}: {reaction_name}")

            # Extract playertext
            optiontext = ""
            match = re.search(r'playertext\s+"([^"]*)"', line)
            if match:
                optiontext = match.group(1)
            else:
                logger.warning(f"No playertext found in option at line {current_line}")

            # Extract linkto
            nodelink = ""
            match = re.search(r'linkto\s+"([^"]*)"', line)
            if match:
                nodelink = match.group(1)
            else:
                logger.warning(f"No linkto found in option at line {current_line}")

            # Extract notes
            notes = ""
            match = re.search(r'notes\s+"([^"]*)"', line)
            if match:
                notes = match.group(1)

            # Extract and parse conditions
            conditions = []
            condition_match = re.search(r'conditions\s*\{([^}]+)\}', line)
            if condition_match:
                conditions_text = condition_match.group(1)
                conditions = self._parse_conditions(conditions_text)
                logger.debug(f"Parsed {len(conditions)} conditions for option at line {current_line}")

            return PlayerOption(
                optiontext=optiontext,
                nodelink=nodelink,
                reaction=reaction,
                intcheck=intcheck,
                notes=notes,
                conditions=conditions,
                conditioncnt=len(conditions)
            )

        except Exception as e:
            logger.error(f"Error parsing option at line {current_line}: {e}")
            raise ValueError(f"Failed to parse option at line {current_line}: {e}") from e

    def _parse_conditions(self, conditions_text: str) -> List[Condition]:
        """Parse conditions from condition text block"""
        conditions = []
        
        # The format is: CHECK_TYPE VAR_NAME OP VALUE [link_next AND|OR|NONE]
        # We need to parse this more carefully
        # Examples:
        #   CHECK_STAT intelligence <= 5 link_next NONE
        #   CHECK_SKILL speech >= 60 link_next AND
        #   LOCAL_VARIABLE Seville_Had_Drugs > 0 link_next NONE
        
        # First, normalize: replace 'link_next' with a delimiter that we can split on
        # But we need to be careful - each condition has an optional link_next
        
        # Use regex to find all condition+link pairs
        # Pattern: (CHECK_\w+)\s+(\w+)\s*(==|>=|<=|>|<)\s*(\w+)\s*(link_next\s+(AND|OR|NONE))?
        
        # More robust approach: iterate through tokens
        tokens = conditions_text.split()
        i = 0
        
        while i < len(tokens):
            # Must start with a condition type
            if tokens[i] not in ('CHECK_STAT', 'CHECK_SKILL', 'CHECK_MONEY', 
                                 'LOCAL_VARIABLE', 'GLOBAL_VARIABLE', 'CHECK_CUSTOM_CODE'):
                i += 1
                continue
            
            check_type_str = tokens[i]
            i += 1
            
            # Determine check type enum
            if check_type_str == 'CHECK_STAT':
                check_type = CheckType.STAT
            elif check_type_str == 'CHECK_SKILL':
                check_type = CheckType.SKILL
            elif check_type_str == 'CHECK_MONEY':
                check_type = CheckType.MONEY
            elif check_type_str == 'LOCAL_VARIABLE':
                check_type = CheckType.LOCAL_VAR
            elif check_type_str == 'GLOBAL_VARIABLE':
                check_type = CheckType.GLOBAL_VAR
            elif check_type_str == 'CHECK_CUSTOM_CODE':
                check_type = CheckType.CUSTOM_CODE
            else:
                check_type = CheckType.STAT
            
            # For custom code, the rest is the code in quotes
            if check_type == CheckType.CUSTOM_CODE:
                # Should be a quoted string
                if i < len(tokens) and tokens[i].startswith('"'):
                    # Collect all tokens until we hit link_next or end
                    code_parts = []
                    while i < len(tokens) and tokens[i] != 'link_next':
                        code_parts.append(tokens[i])
                        i += 1
                    # Join and extract from quotes
                    code_str = ' '.join(code_parts)
                    code_match = re.match(r'"([^"]*)"', code_str)
                    if code_match:
                        var_ptr = ""
                        check_value = code_match.group(1)
                        check_eval = CompareType.EQUAL
                        check_field = 0
                    else:
                        i += 1
                        continue
                else:
                    i += 1
                    continue
            else:
                # Regular condition: VAR_NAME OP VALUE
                if i >= len(tokens):
                    break
                    
                var_ptr = tokens[i]
                i += 1
                
                if i >= len(tokens):
                    break
                    
                op_str = tokens[i]
                i += 1
                
                if i >= len(tokens):
                    break
                    
                check_value = tokens[i]
                i += 1
                
                # Map operator to CompareType
                if op_str == '==':
                    check_eval = CompareType.EQUAL
                elif op_str == '!=':
                    check_eval = CompareType.NOT_EQUAL
                elif op_str == '>':
                    check_eval = CompareType.LARGER_THAN
                elif op_str == '<':
                    check_eval = CompareType.LESS_THAN
                elif op_str == '>=':
                    check_eval = CompareType.LARGER_EQUAL
                elif op_str == '<=':
                    check_eval = CompareType.LESS_EQUAL
                else:
                    check_eval = CompareType.EQUAL
                
                # Map stat/skill names to field numbers
                check_field = self._get_stat_field_number(var_ptr) if check_type == CheckType.STAT else 0
            
            # Check for link_next
            link = LinkType.NONE
            if i < len(tokens) and tokens[i] == 'link_next':
                i += 1  # skip 'link_next'
                if i < len(tokens):
                    link_str = tokens[i].upper()
                    if link_str == 'AND':
                        link = LinkType.AND
                    elif link_str == 'OR':
                        link = LinkType.OR
                    else:
                        link = LinkType.NONE
                    i += 1
            
            condition = Condition(
                check_type=check_type,
                check_field=check_field,
                check_eval=check_eval,
                var_ptr=var_ptr,
                check_value=check_value,
                link=link
            )
            conditions.append(condition)
        
        return conditions

    def _get_stat_field_number(self, stat_name: str) -> int:
        """Get the field number for a stat name"""
        stat_map = {
            'strength': 0,
            'perception': 1,
            'endurance': 2,
            'charisma': 3,
            'intelligence': 4,
            'agility': 5,
            'luck': 6,
            'dude_caps': 7,  # Money
            'level': 8,
            'cur_poison_lev': 9,
            'cur_rad_lev': 10,
        }
        return stat_map.get(stat_name.lower(), 0)

    def get_last_detected_encoding(self) -> Optional[str]:
        """Return the last detected encoding from load_from_file"""
        return self._last_detected_encoding

    def write_fmf(self, dialogue: Dialogue, stream: TextIO) -> None:
        """Write dialogue to FMF format with Unicode support"""
        # Write header
        stream.write('/*\n\n    Fan Made Fallout Dialogue Tool\n         dialogue script file\n\n -- hand editing this file is not recommended\n\n Created with version 2.0.0-dev\n\n*/\n\n')

        # Write global properties
        stream.write(f'NPCName "{dialogue.npcname}"\n')
        stream.write(f'Location "{dialogue.location}"\n')
        stream.write(f'Description "{dialogue.description}"\n')
        stream.write(f'Unknown_Desc "{dialogue.unknowndesc}"\n')
        stream.write(f'Known_Desc "{dialogue.knowndesc}"\n')
        stream.write(f'Detailed_Desc "{dialogue.detaileddesc}"\n')
        
        # Write NPC timing properties
        if dialogue.start_time_event > 0:
            stream.write(f'\n/* Timing */\n')
            stream.write(f'StartTimeEvent {dialogue.start_time_event}\n')
        
        # Write starting conditions
        if dialogue.startconditions and len(dialogue.startconditions) > 0:
            stream.write('\n/* Dialogue starting conditions */\n')
            for start_cond in dialogue.startconditions:
                if start_cond.conditions and len(start_cond.conditions) > 0:
                    conditions_str = self._write_conditions(start_cond.conditions)
                    stream.write(f'StartCondition "{start_cond.goto_node}" conditions {{ {conditions_str} }}\n')
        
        # Write custom procedures
        if dialogue.customprocs and len(dialogue.customprocs) > 0:
            stream.write('\n/* Custom procedures */\n')
            for proc in dialogue.customprocs:
                proc_associate = proc.associatewithnode if proc.associatewithnode > 0 else 0
                stream.write(f'CustomProc "{proc.name}" associate {proc_associate}\n')
                if proc.lines:
                    stream.write(f'{{\n{proc.lines}\n}}\n')
        
        # Write timed events
        if dialogue.timedevents and len(dialogue.timedevents) > 0:
            stream.write('\n/* Timed events */\n')
            for event in dialogue.timedevents:
                interval_str = f"{event.mininterval},{event.maxinterval}" if event.israndom else str(event.interval)
                random_str = " random" if event.israndom else ""
                stream.write(f'TimedEvent "{event.fixedparamname}" interval={interval_str}{random_str}\n')
                if event.actionlines and len(event.actionlines) > 0:
                    stream.write('{\n')
                    for action in event.actionlines:
                        if action.linedata:
                            stream.write(f'  {action.linedata}\n')
                    stream.write('}\n')
        
        # Write variables
        if dialogue.variables and len(dialogue.variables) > 0:
            stream.write('\n/* Variables */\n')
            for var in dialogue.variables:
                var_flags = ''
                if var.flags == 1:
                    var_flags = 'import '
                elif var.flags == 2:
                    var_flags = 'export '
                elif var.flags == 3:
                    var_flags = 'local '
                elif var.flags == 4:
                    var_flags = 'global '
                
                var_type_str = ''
                if var.vartype == 0:
                    var_type_str = ' string'
                elif var.vartype == 1:
                    var_type_str = ' int'
                elif var.vartype == 2:
                    var_type_str = ' float'
                
                notes_str = f' // {var.notes}' if var.notes else ''
                stream.write(f'Variable{var_flags}"{var.name}"{var_type_str} = {var.value}{notes_str}\n')
        
        stream.write('\n')

        # Write float message nodes
        if dialogue.floatnodes and len(dialogue.floatnodes) > 0:
            stream.write('/* Float nodes */\n')
            for float_node in dialogue.floatnodes:
                stream.write(f'FloatNode "{float_node.nodename}"\n')
                stream.write(f'notes "{float_node.notes}"\n')
                stream.write('{\n')
                if float_node.messages and len(float_node.messages) > 0:
                    for msg in float_node.messages:
                        stream.write(f'  message "{msg}"\n')
                stream.write('}\n\n')

        # Write regular dialogue nodes
        stream.write('/* Regular nodes */\n')
        for node in dialogue.nodes:
            stream.write(f'Node "{node.nodename}"\n')
            stream.write(f'notes "{node.notes}"\n')
            stream.write(f'is_wtg = {str(node.is_wtg).lower()}\n')
            stream.write('{\n')
            stream.write(f'NPCText "{node.npctext}"\n')
            if node.npctext_female:
                stream.write(f'NPCFEMALETEXT "{node.npctext_female}"\n')

            if node.options:
                stream.write('      options {\n')
                for option in node.options:
                    reaction_name = option.reaction.name if hasattr(option.reaction, 'name') else 'NEUTRAL'
                    
                    # Build the conditions string if conditions exist
                    conditions_str = ''
                    if option.conditions and len(option.conditions) > 0:
                        conditions_str = ' conditions { ' + self._write_conditions(option.conditions) + ' }'
                    
                    stream.write(f'          int={option.intcheck} Reaction=REACTION_{reaction_name} playertext "{option.optiontext}" linkto "{option.nodelink}"{conditions_str} notes "{option.notes}"\n')
                stream.write('              }\n')

            stream.write('}\n\n')

    def _write_conditions(self, conditions: List[Condition]) -> str:
        """Convert a list of conditions to FMF format string"""
        result_parts = []
        
        for idx, cond in enumerate(conditions):
            # Determine check type string
            if cond.check_type == CheckType.STAT:
                check_type_str = 'CHECK_STAT'
            elif cond.check_type == CheckType.SKILL:
                check_type_str = 'CHECK_SKILL'
            elif cond.check_type == CheckType.MONEY:
                check_type_str = 'CHECK_MONEY'
            elif cond.check_type == CheckType.LOCAL_VAR:
                check_type_str = 'LOCAL_VARIABLE'
            elif cond.check_type == CheckType.GLOBAL_VAR:
                check_type_str = 'GLOBAL_VARIABLE'
            elif cond.check_type == CheckType.CUSTOM_CODE:
                check_type_str = 'CHECK_CUSTOM_CODE'
            else:
                check_type_str = 'CHECK_STAT'
            
            # Determine operator string
            if cond.check_eval == CompareType.EQUAL:
                op_str = ' == '
            elif cond.check_eval == CompareType.NOT_EQUAL:
                op_str = ' != '
            elif cond.check_eval == CompareType.LARGER_THAN:
                op_str = ' > '
            elif cond.check_eval == CompareType.LESS_THAN:
                op_str = ' < '
            elif cond.check_eval == CompareType.LARGER_EQUAL:
                op_str = ' >= '
            elif cond.check_eval == CompareType.LESS_EQUAL:
                op_str = ' <= '
            else:
                op_str = ' == '
            
            # Format the condition
            if cond.check_type == CheckType.CUSTOM_CODE:
                # Custom code: CHECK_CUSTOM_CODE "code"
                cond_str = f'{check_type_str} "{cond.check_value}"'
            else:
                # Regular condition: CHECK_TYPE VAR_NAME OP VALUE
                cond_str = f'{check_type_str} {cond.var_ptr}{op_str}{cond.check_value}'
            
            result_parts.append(cond_str)
            
            # Add link_next if there's a next condition
            if idx < len(conditions) - 1:
                next_link = conditions[idx + 1].link if idx + 1 < len(conditions) else LinkType.NONE
                if next_link == LinkType.AND:
                    result_parts.append('link_next AND')
                elif next_link == LinkType.OR:
                    result_parts.append('link_next OR')
                else:
                    result_parts.append('link_next NONE')
            else:
                # Last condition
                result_parts.append('link_next NONE')
        
        return ' '.join(result_parts)

    def _parse_start_condition(self, line: str) -> Optional['StartingCondition']:
        """Parse a starting condition from the FMF format"""
        try:
            # Format: StartCondition "goto_node" conditions { conditions_text }
            match = re.search(r'StartCondition\s+"([^"]+)"', line)
            if not match:
                return None
            
            start_cond = StartingCondition()
            start_cond.goto_node = match.group(1)
            
            # Parse conditions if present
            condition_match = re.search(r'conditions\s*\{([^}]+)\}', line)
            if condition_match:
                conditions_text = condition_match.group(1)
                start_cond.conditions = self._parse_conditions(conditions_text)
                start_cond.condcnt = len(start_cond.conditions)
            
            return start_cond
        except Exception as e:
            logger.warning(f"Error parsing start condition: {e}")
            return None

    def _parse_custom_proc(self, lines: List[str], start_idx: int) -> tuple:
        """Parse a custom procedure from the FMF format"""
        try:
            line = lines[start_idx].strip()
            # Format: CustomProc "name" associate N
            match = re.search(r'CustomProc\s+"([^"]+)"\s+associate\s+(\d+)', line)
            if not match:
                return None, start_idx
            
            proc = CustomProcedure()
            proc.name = match.group(1)
            proc.associatewithnode = int(match.group(2))
            
            # Check for procedure body
            i = start_idx + 1
            while i < len(lines):
                line_content = lines[i].strip()
                if line_content == '{':
                    # Parse body until closing brace
                    i += 1
                    body_lines = []
                    while i < len(lines):
                        body_line = lines[i].strip()
                        if body_line == '}':
                            break
                        body_lines.append(body_line)
                        i += 1
                    proc.lines = '\n'.join(body_lines)
                    break
                elif line_content.startswith('Node ') or line_content.startswith('FloatNode') or line_content.startswith('CustomProc'):
                    break
                i += 1
            
            return proc, i
        except Exception as e:
            logger.warning(f"Error parsing custom procedure: {e}")
            return None, start_idx

    def _parse_timed_event(self, lines: List[str], start_idx: int) -> tuple:
        """Parse a timed event from the FMF format"""
        try:
            line = lines[start_idx].strip()
            # Format: TimedEvent "name" interval=N or interval=N,M random
            match = re.search(r'TimedEvent\s+"([^"]+)"\s+interval=([\d,]+)(?:\s+random)?', line)
            if not match:
                return None, start_idx
            
            event = TimeEvent()
            event.fixedparamname = match.group(1)
            
            interval_str = match.group(2)
            if ',' in interval_str:
                parts = interval_str.split(',')
                event.israndom = True
                event.mininterval = int(parts[0])
                event.maxinterval = int(parts[1])
            else:
                event.interval = int(interval_str)
            
            # Check for action body
            i = start_idx + 1
            while i < len(lines):
                line_content = lines[i].strip()
                if line_content == '{':
                    # Parse actions
                    i += 1
                    while i < len(lines):
                        action_line = lines[i].strip()
                        if action_line == '}':
                            break
                        if action_line:
                            action = Action()
                            action.linedata = action_line
                            event.actionlines.append(action)
                            event.actioncnt += 1
                        i += 1
                elif line_content.startswith('Node ') or line_content.startswith('FloatNode'):
                    break
                i += 1
            
            return event, i
        except Exception as e:
            logger.warning(f"Error parsing timed event: {e}")
            return None, start_idx

    def _parse_variable(self, line: str) -> Optional['Variable']:
        """Parse a variable from the FMF format"""
        try:
            # Format: Variable[flags]"name"[type] = value // notes
            # Flags: import, export, local, global
            # Type: string, int, float
            
            flags = 0
            if 'import' in line:
                flags = 1
            elif 'export' in line:
                flags = 2
            elif 'local' in line:
                flags = 3
            elif 'global' in line:
                flags = 4
            
            vartype = 1  # default int
            if 'string' in line:
                vartype = 0
            elif 'float' in line:
                vartype = 2
            
            name_match = re.search(r'"([^"]+)"', line)
            if not name_match:
                return None
            
            var = Variable()
            var.name = name_match.group(1)
            var.flags = flags
            var.vartype = vartype
            
            # Parse value
            value_match = re.search(r'=\s*(.+?)(?://|$)', line)
            if value_match:
                value_str = value_match.group(1).strip()
                # Remove trailing semicolon if present
                value_str = value_str.rstrip(';')
                if vartype == 2:  # float
                    try:
                        var.value = float(value_str)
                    except ValueError:
                        var.value = 0.0
                elif vartype == 1:  # int
                    try:
                        var.value = int(value_str)
                    except ValueError:
                        var.value = 0
                else:  # string
                    var.value = value_str.strip('"')
            
            # Parse notes (comment)
            notes_match = re.search(r'//\s*(.+)$', line)
            if notes_match:
                var.notes = notes_match.group(1).strip()
            
            return var
        except Exception as e:
            logger.warning(f"Error parsing variable: {e}")
            return None

    def _parse_float_node(self, lines: List[str], start_idx: int) -> tuple:
        """Parse a float node from the FMF format"""
        try:
            line = lines[start_idx].strip()
            # Format: FloatNode "nodename"
            match = re.search(r'FloatNode\s+"([^"]+)"', line)
            if not match:
                return None, start_idx
            
            float_node = FloatNode()
            float_node.nodename = match.group(1)
            
            # Parse notes and body
            i = start_idx + 1
            while i < len(lines):
                line_content = lines[i].strip()
                
                if line_content.startswith('notes'):
                    float_node.notes = self._parse_quoted_string(line_content)
                elif line_content == '{':
                    # Parse messages
                    i += 1
                    while i < len(lines):
                        msg_line = lines[i].strip()
                        if msg_line == '}':
                            # Move past the closing brace
                            i += 1
                            break
                        if msg_line.startswith('message'):
                            msg = self._parse_quoted_string(msg_line)
                            if msg:
                                float_node.messages.append(msg)
                                float_node.messagecnt += 1
                        i += 1
                elif line_content.startswith('Node ') or line_content.startswith('FloatNode'):
                    # Don't increment - return this index so it can be processed
                    return float_node, i
                i += 1
            
            return float_node, i
        except Exception as e:
            logger.warning(f"Error parsing float node: {e}")
            return None, start_idx
