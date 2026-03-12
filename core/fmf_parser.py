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

class FMFParser(QObject):
    """Parser for FMF dialogue files (text format)"""

    # Progress signals
    progress_updated = pyqtSignal(int, str)  # progress percentage, current operation

    def __init__(self):
        super().__init__()
        self.current_dialogue: Optional[Dialogue] = None

    def load_from_file(self, file_path: Path) -> Dialogue:
        """Load dialogue from FMF file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return self.parse_fmf(f)
        except Exception as e:
            logger.error(f"Failed to load FMF file {file_path}: {e}")
            raise

    def save_to_file(self, dialogue: Dialogue, file_path: Path) -> None:
        """Save dialogue to FMF file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
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
                    elif line.startswith('Node '):
                        # Start parsing nodes
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

            return PlayerOption(
                optiontext=optiontext,
                nodelink=nodelink,
                reaction=reaction,
                intcheck=intcheck,
                notes=notes
            )

        except Exception as e:
            logger.error(f"Error parsing option at line {current_line}: {e}")
            raise ValueError(f"Failed to parse option at line {current_line}: {e}") from e

    def write_fmf(self, dialogue: Dialogue, stream: TextIO) -> None:
        """Write dialogue to FMF format"""
        # Write header
        stream.write('/*\n\n    Fan Made Fallout Dialogue Tool\n         dialogue script file\n\n -- hand editing this file is not recommended\n\n Created with version 2.0.0-dev\n\n*/\n\n')

        # Write global properties
        stream.write(f'NPCName "{dialogue.npcname}"\n')
        stream.write(f'Location "{dialogue.location}"\n')
        stream.write(f'Description "{dialogue.description}"\n')
        stream.write(f'Unknown_Desc "{dialogue.unknowndesc}"\n')
        stream.write(f'Known_Desc "{dialogue.knowndesc}"\n')
        stream.write(f'Detailed_Desc "{dialogue.detaileddesc}"\n')
        stream.write('\n')

        # Write nodes
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
                    stream.write(f'          int={option.intcheck} Reaction=REACTION_{reaction_name} playertext "{option.optiontext}" linkto "{option.nodelink}"  notes "{option.notes}"\n')
                stream.write('              }\n')

            stream.write('}\n\n')