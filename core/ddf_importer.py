"""
DDF (Dialogue Definition Format) Importer

Provides functionality to import DDF files into Dialogue objects.
Supports parsing of all DDF sections with validation and error handling.

DDF Format Structure:
- Header comments (/* ... */)
- Output file declarations (MSGOutputName, SCROutputName, etc.)
- NPC metadata (NPCName, Description, Location)
- Description procedure (descproc)
- Start nodes (StartNodes)
- Variable definitions
- Dialogue nodes
- Timed events
"""

import re
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from models.dialogue import (
    Dialogue, DialogueNode, PlayerOption, Condition,
    SkillCheck, FloatNode, TimeEvent, Action, Variable,
    StartingCondition, CustomProcedure, CheckType, CompareType, 
    LinkType, Reaction, Gender
)
from core.import_base import (
    ImportResult, ImportProgress, ImportProgressReporter,
    ImportValidator, ImportIssue, ImportLevel, log_import_exception
)

logger = logging.getLogger(__name__)


class DDFSection(Enum):
    """Known DDF sections"""
    UNKNOWN = 0
    HEADER = 1
    OUTPUT_PATHS = 2
    METADATA = 3
    DESCRIPTION_PROC = 4
    START_NODES = 5
    VARIABLES = 6
    TIMED_EVENTS = 7
    DIALOGUE_NODES = 8
    FLOAT_NODES = 9


@dataclass
class DDFParseContext:
    """Context for parsing DDF files"""
    current_section: DDFSection = DDFSection.UNKNOWN
    line_number: int = 0
    current_node: Optional[DialogueNode] = None
    current_float_node: Optional[FloatNode] = None
    current_skill_check: Optional[SkillCheck] = None
    in_procedure: bool = False
    procedure_buffer: List[str] = field(default_factory=list)
    brace_depth: int = 0
    
    # Parsed data
    msg_output_name: str = ""
    ssl_output_name: str = ""
    script_template: str = ""
    script_id: str = ""


class DDFImportValidator(ImportValidator):
    """Validator for DDF import"""
    
    def __init__(self):
        super().__init__()
        self.node_names: Dict[str, int] = {}  # Track node names to detect duplicates
    
    def validate_dialogue(self, dialogue: Dialogue) -> bool:
        """Validate a parsed dialogue"""
        self.clear()
        
        # Check required fields
        if not dialogue.npcname:
            self.add_validation_warning("NPC name is empty, using default")
        
        # Check for duplicate node names
        for node in dialogue.nodes:
            if node.nodename in self.node_names:
                self.add_validation_error(f"Duplicate node name: {node.nodename}")
            else:
                self.node_names[node.nodename] = 1
                
            # Validate node links
            for option in node.options:
                if option.nodelink and not option.nodelink.startswith('done') and \
                   option.nodelink not in self.node_names:
                    self.add_validation_warning(
                        f"Node '{node.nodename}' has invalid link to: {option.nodelink}"
                    )
        
        # Validate start conditions
        for cond in dialogue.startconditions:
            if cond.goto_node and cond.goto_node not in self.node_names:
                self.add_validation_warning(
                    f"Start condition links to non-existent node: {cond.goto_node}"
                )
        
        return len(self.errors) == 0
    
    def validate_node(self, node: DialogueNode, line_number: int) -> bool:
        """Validate a single dialogue node"""
        if not node.nodename:
            self.add_validation_error(f"Node missing name", line_number=line_number)
            return False
        
        if not node.npctext and not node.is_wtg:
            self.add_validation_warning(
                f"Node '{node.nodename}' has no NPC text",
                line_number=line_number
            )
        
        return True


class DDFImporter:
    """Importer for DDF format files"""
    
    # Regular expressions for parsing DDF
    RE_COMMENT = re.compile(r'/\*.*?\*/', re.DOTALL)
    RE_SINGLE_LINE_COMMENT = re.compile(r'//.*$')
    RE_SECTION = re.compile(r'^\[(\w+)\]$')
    RE_KEY_VALUE = re.compile(r'^(\w+)\s*=\s*(.*)$')
    RE_NODE_START = re.compile(r'^node\s+(\w+)\s*(?:\((.*?)\))?\s*;$', re.IGNORECASE)
    RE_OPTION = re.compile(r'^\{(.*?)\}\s*"(.*?)"\s*->\s*(\w+)\s*;?$', re.DOTALL)
    RE_SKILL_CHECK = re.compile(r'^skillcheck\s+(\w+)\s*(\d+)\s*->\s*(\w+)\s*,\s*(\w+)\s*;?$', re.IGNORECASE)
    RE_CONDITION = re.compile(r'^\((.*?)\)(?:\s+(and|or)\s+\((.*?)\))*$', re.IGNORECASE)
    RE_VARIABLE = re.compile(r'^variable(\w+)?(\w+)\s*(?:\((.*?)\))?\s*(?:=\s*(.*))?;?$', re.IGNORECASE)
    RE_PROCEDURE_START = re.compile(r'^(descproc|proc)\s+(\w+)\s*;?$', re.IGNORECASE)
    RE_PROCEDURE_END = re.compile(r'^end;?$', re.IGNORECASE)
    RE_START_NODES = re.compile(r'^StartNodes\s+Begin$', re.IGNORECASE)
    RE_CASE = re.compile(r'^Case\s+(.+?):\s*(\w+)\s+EndCase$', re.IGNORECASE)
    RE_DEFAULT = re.compile(r'^Case\s+\(default\):\s*(\w+)\s+EndCase$', re.IGNORECASE)
    RE_TIMED_EVENT = re.compile(r'^timedevent\s+(\w+)\s*;?$', re.IGNORECASE)
    RE_FLOAT_NODE = re.compile(r'^floatnode\s+(\w+)\s*;?$', re.IGNORECASE)
    RE_WTG = re.compile(r'wtg\s+"(.*?)"\s*;', re.IGNORECASE)
    RE_CUSTOM_CODE = re.compile(r'customcode\s+"(.*?)"\s*;', re.IGNORECASE)
    
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
        self.validator = DDFImportValidator()
        self.progress = ImportProgressReporter()
        self._current_dialogue: Optional[Dialogue] = None
        self._context: Optional[DDFParseContext] = None
    
    def import_file(self, file_path: Path) -> Tuple[Optional[Dialogue], ImportResult]:
        """
        Import a DDF file.
        
        Args:
            file_path: Path to the DDF file
            
        Returns:
            Tuple of (Dialogue object or None, ImportResult)
        """
        result = ImportResult(success=False)
        
        logger.info(f"Starting DDF import from: {file_path}")
        
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
            
            # Pre-process content
            processed_content = self._preprocess_content(content)
            
            # Parse content
            dialogue = self._parse_content(processed_content, result)
            if dialogue is None:
                return None, result
            
            # Validate parsed dialogue
            if not self.validator.validate_dialogue(dialogue):
                for error in self.validator.errors:
                    result.add_error(error.message, error.line_number)
                for warning in self.validator.warnings:
                    result.add_warning(warning.message, warning.line_number)
            
            # Resolve node links
            dialogue.resolve_nodes()
            
            result.success = True
            result.imported_count = dialogue.nodecount
            
            logger.info(f"DDF import completed successfully: {dialogue.nodecount} nodes")
            return dialogue, result
            
        except Exception as e:
            error_msg = log_import_exception(logger, f"importing DDF file {file_path}")
            result.add_error(error_msg)
            return None, result
    
    def import_multiple(self, file_paths: List[Path], 
                       transaction_name: str = "ddf_import") -> Tuple[List[Dialogue], ImportResult]:
        """
        Import multiple DDF files with transaction support.
        
        Args:
            file_paths: List of paths to DDF files
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
                    logger.error(f"Non-recoverable error in {file_path}, stopping import")
                    break
        
        self.progress.update(len(file_paths), len(file_paths), "", "Import complete")
        
        result.total_count = len(file_paths)
        return dialogues, result
    
    def _read_file(self, file_path: Path) -> Optional[str]:
        """Read file with encoding detection"""
        # Try UTF-8 first
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            pass
        
        # Try other common encodings
        for encoding in ['cp1252', 'iso-8859-1', 'latin1']:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        
        # Try to read as binary and decode
        try:
            raw_data = file_path.read_bytes()
            # Try to decode with error replacement
            return raw_data.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Failed to read file with any encoding: {e}")
            return None
    
    def _preprocess_content(self, content: str) -> str:
        """Pre-process DDF content"""
        # Remove multi-line comments
        content = self.RE_COMMENT.sub('', content)
        
        # Remove single-line comments
        content = self.RE_SINGLE_LINE_COMMENT.sub('', content)
        
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove empty lines at start/end
        content = content.strip()
        
        return content
    
    def _parse_content(self, content: str, result: ImportResult) -> Optional[Dialogue]:
        """Parse pre-processed DDF content"""
        self._current_dialogue = Dialogue()
        self._context = DDFParseContext()
        
        lines = content.split('\n')
        total_lines = len(lines)
        
        for line_num, line in enumerate(lines):
            self._context.line_number = line_num + 1
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Update progress periodically
            if line_num % 100 == 0:
                self.progress.update(line_num, total_lines, "", "Parsing")
            
            # Parse based on current section
            try:
                self._parse_line(line, result)
            except Exception as e:
                result.add_warning(
                    f"Error parsing line: {e}",
                    line_number=line_num + 1
                )
                logger.debug(f"Parse error at line {line_num + 1}: {line} - {e}")
        
        return self._current_dialogue
    
    def _parse_line(self, line: str, result: ImportResult):
        """Parse a single line of DDF content"""
        ctx = self._context
        
        # Check for section headers
        if line.startswith('[') and line.endswith(']'):
            self._handle_section(line, result)
            return
        
        # Handle key-value pairs
        kv_match = self.RE_KEY_VALUE.match(line)
        if kv_match:
            self._handle_key_value(kv_match.group(1), kv_match.group(2), result)
            return
        
        # Handle node definitions
        if line.lower().startswith('node '):
            self._handle_node_start(line, result)
            return
        
        # Handle player options
        if line.startswith('{'):
            self._handle_option(line, result)
            return
        
        # Handle WTG (what to say)
        wtg_match = self.RE_WTG.match(line)
        if wtg_match:
            self._handle_wtg(wtg_match.group(1), result)
            return
        
        # Handle custom code
        custom_match = self.RE_CUSTOM_CODE.match(line)
        if custom_match:
            self._handle_custom_code(custom_match.group(1), result)
            return
        
        # Handle skill check
        if line.lower().startswith('skillcheck'):
            self._handle_skill_check(line, result)
            return
        
        # Handle skill check end
        if line.lower() == 'endskillcheck;':
            self._handle_skill_check_end(result)
            return
        
        # Handle description procedure
        if line.lower().startswith('descproc'):
            ctx.in_procedure = True
            ctx.current_section = DDFSection.DESCRIPTION_PROC
            return
        
        # Handle procedure end
        if line.lower() in ('end;', 'end'):
            if ctx.in_procedure:
                ctx.in_procedure = False
            return
        
        # Handle start nodes
        if self.RE_START_NODES.match(line):
            ctx.current_section = DDFSection.START_NODES
            return
        
        # Handle case statements
        case_match = self.RE_CASE.match(line)
        if case_match:
            self._handle_case(case_match.group(1), case_match.group(2), result)
            return
        
        default_match = self.RE_DEFAULT.match(line)
        if default_match:
            self._handle_default_case(default_match.group(1), result)
            return
        
        # Handle variable definitions
        if line.lower().startswith('variable'):
            self._handle_variable(line, result)
            return
        
        # Handle timed events
        if line.lower().startswith('timedevent'):
            self._handle_timed_event(line, result)
            return
        
        # Handle float nodes
        if line.lower().startswith('floatnode'):
            self._handle_float_node(line, result)
            return
        
        # Handle message definitions within nodes
        if ctx.current_node and '=' in line:
            self._handle_node_property(line, result)
    
    def _handle_section(self, line: str, result: ImportResult):
        """Handle section headers"""
        section_name = line[1:-1].lower()
        
        if 'output' in section_name or 'path' in section_name:
            self._context.current_section = DDFSection.OUTPUT_PATHS
        elif section_name == 'metadata' or 'npc' in section_name:
            self._context.current_section = DDFSection.METADATA
        elif 'descproc' in section_name or 'description' in section_name:
            self._context.current_section = DDFSection.DESCRIPTION_PROC
        elif 'start' in section_name:
            self._context.current_section = DDFSection.START_NODES
        elif 'variable' in section_name:
            self._context.current_section = DDFSection.VARIABLES
        elif 'timed' in section_name or 'event' in section_name:
            self._context.current_section = DDFSection.TIMED_EVENTS
        elif 'node' in section_name:
            self._context.current_section = DDFSection.DIALOGUE_NODES
        elif 'float' in section_name:
            self._context.current_section = DDFSection.FLOAT_NODES
        else:
            self._context.current_section = DDFSection.UNKNOWN
        
        logger.debug(f"Section: {section_name}")
    
    def _handle_key_value(self, key: str, value: str, result: ImportResult):
        """Handle key-value pairs"""
        key_lower = key.lower().strip()
        value = value.strip().strip('"')
        
        dialogue = self._current_dialogue
        
        if key_lower == 'msgoutputname':
            self._context.msg_output_name = value
        elif key_lower == 'scroputname' or key_lower == 'ssloutputname':
            self._context.ssl_output_name = value
        elif key_lower == 'scripttemplate':
            self._context.script_template = value
        elif key_lower == 'scriptid':
            self._context.script_id = value
        elif key_lower == 'npcname':
            dialogue.npcname = value
        elif key_lower == 'description':
            dialogue.description = value
        elif key_lower == 'location':
            dialogue.location = value
        elif key_lower == 'unknown':
            dialogue.unknowndesc = value
        elif key_lower == 'known':
            dialogue.knowndesc = value
        elif key_lower == 'detailed':
            dialogue.detaileddesc = value
    
    def _handle_node_start(self, line: str, result: ImportResult):
        """Handle start of a dialogue node"""
        match = self.RE_NODE_START.match(line)
        if not match:
            return
        
        node_name = match.group(1)
        
        # Check for node attributes in parentheses
        attrs = match.group(2)
        
        node = DialogueNode()
        node.nodename = node_name
        
        if attrs:
            if 'wtg' in attrs.lower() or 'start' in attrs.lower():
                node.is_wtg = True
        
        self._current_dialogue.nodes.append(node)
        self._current_dialogue.nodecount += 1
        self._context.current_node = node
        
        logger.debug(f"Created node: {node_name}")
    
    def _handle_option(self, line: str, result: ImportResult):
        """Handle player option"""
        if not self._context.current_node:
            result.add_warning("Option outside of node", line_number=self._context.line_number)
            return
        
        # Parse option line: {conditions} "text" -> node;
        match = re.match(r'\{(.*?)\}\s*"(.*?)"\s*->\s*(\w+)\s*;?', line)
        if not match:
            # Try simpler format: "text" -> node;
            match = re.match(r'"(.*?)"\s*->\s*(\w+)\s*;?', line)
            if not match:
                result.add_warning(f"Could not parse option: {line}", 
                                  line_number=self._context.line_number)
                return
        
        if len(match.groups()) == 3:
            conditions_str = match.group(1)
            option_text = match.group(2)
            node_link = match.group(3)
        else:
            conditions_str = ""
            option_text = match.group(1)
            node_link = match.group(2)
        
        option = PlayerOption()
        option.optiontext = option_text
        option.nodelink = node_link
        
        # Parse conditions
        if conditions_str:
            option.conditions = self._parse_conditions(conditions_str)
            option.conditioncnt = len(option.conditions)
        
        self._context.current_node.options.append(option)
        self._context.current_node.optioncnt += 1
    
    def _parse_conditions(self, conditions_str: str) -> List[Condition]:
        """Parse condition string into Condition objects"""
        conditions = []
        
        # Split by 'and' or 'or'
        parts = re.split(r'\s+(and|or)\s+', conditions_str, flags=re.IGNORECASE)
        
        for i, part in enumerate(parts):
            if part.lower() in ('and', 'or'):
                continue
            
            part = part.strip().strip('()')
            
            # Try to parse the condition
            # Format: skill_xxx >= value or stat_xxx <= value etc.
            # Use defaults for required fields
            cond = Condition(
                check_type=CheckType.CUSTOM_CODE,
                check_field=0,
                check_eval=CompareType.EQUAL
            )
            
            if 'skill_' in part.lower():
                cond.check_type = CheckType.SKILL
                # Parse skill check
                skill_match = re.match(r'skill_(\w+)\s*([<>=]+)\s*(\d+)', part, re.IGNORECASE)
                if skill_match:
                    cond.check_field = self._parse_skill_name(skill_match.group(1))
                    cond.check_value = skill_match.group(3)
                    cond.resolved_code = part
            elif 'stat_' in part.lower():
                cond.check_type = CheckType.STAT
                # Parse stat check
                stat_match = re.match(r'stat_(\w+)\s*([<>=]+)\s*(\d+)', part, re.IGNORECASE)
                if stat_match:
                    cond.check_field = self._parse_stat_name(stat_match.group(1))
                    cond.check_value = stat_match.group(3)
                    cond.resolved_code = part
            elif 'global(' in part.lower():
                cond.check_type = CheckType.GLOBAL_VAR
                cond.resolved_code = part
            elif 'money' in part.lower():
                cond.check_type = CheckType.MONEY
                cond.resolved_code = part
            
            # Set link type
            if i > 0:
                prev_link = parts[i - 1].lower() if i > 0 else ""
                if prev_link == 'and':
                    cond.link = LinkType.AND
                elif prev_link == 'or':
                    cond.link = LinkType.OR
            
            conditions.append(cond)
        
        return conditions
    
    def _parse_skill_name(self, name: str) -> int:
        """Parse skill name to value"""
        skill_map = {
            'small_guns': 0, 'big_guns': 1, 'energy_weapons': 2,
            'unarmed': 3, 'melee_weapons': 4, 'throwing': 5,
            'first_aid': 6, 'doctor': 7, 'sneak': 8,
            'lockpick': 9, 'steal': 10, 'traps': 11,
            'science': 12, 'repair': 13, 'speech': 14,
            'barter': 15, 'gambling': 16, 'outdoorsman': 17
        }
        return skill_map.get(name.lower(), 0)
    
    def _parse_stat_name(self, name: str) -> int:
        """Parse stat name to value"""
        stat_map = {
            'st': 0, 'pe': 1, 'en': 2, 'ch': 3, 'in': 4, 'ag': 5, 'lk': 6
        }
        return stat_map.get(name.lower(), 0)
    
    def _handle_wtg(self, text: str, result: ImportResult):
        """Handle WTG (what to say) text"""
        if self._context.current_node:
            self._context.current_node.npctext = text
    
    def _handle_custom_code(self, code: str, result: ImportResult):
        """Handle custom code in node"""
        if self._context.current_node:
            self._context.current_node.customcode = code
    
    def _handle_skill_check(self, line: str, result: ImportResult):
        """Handle skill check definition"""
        match = re.match(
            r'skillcheck\s+(\w+)\s*(\d+)\s*->\s*(\w+)\s*,\s*(\w+)\s*;?',
            line, re.IGNORECASE
        )
        if not match:
            return
        
        skill_check = SkillCheck()
        skill_check.check_what = Skill(int(match.group(2)))
        skill_check.required_value = int(match.group(2))
        skill_check.successnode = match.group(3)
        skill_check.failurenode = match.group(4)
        
        if self._context.current_node:
            self._context.current_node.skillchecks.append(skill_check)
            self._context.current_node.skillcheckcnt += 1
            self._context.current_node.has_skill_check = True
    
    def _handle_skill_check_end(self, result: ImportResult):
        """Handle end of skill check"""
        self._context.current_skill_check = None
    
    def _handle_case(self, condition: str, goto_node: str, result: ImportResult):
        """Handle case statement in start nodes"""
        start_cond = StartingCondition()
        start_cond.goto_node = goto_node
        start_cond.conditions = self._parse_conditions(condition)
        start_cond.condcnt = len(start_cond.conditions)
        
        self._current_dialogue.startconditions.append(start_cond)
        self._current_dialogue.startconditioncnt += 1
    
    def _handle_default_case(self, goto_node: str, result: ImportResult):
        """Handle default case in start nodes"""
        start_cond = StartingCondition()
        start_cond.goto_node = goto_node
        self._current_dialogue.startconditions.append(start_cond)
        self._current_dialogue.startconditioncnt += 1
        self._current_dialogue.default_cond = len(self._current_dialogue.startconditions) - 1
    
    def _handle_variable(self, line: str, result: ImportResult):
        """Handle variable definition"""
        match = re.match(r'variable(\w+)?(\w+)\s*(?:\((.*?)\))?\s*(?:=\s*(.*))?;?', line, re.IGNORECASE)
        if not match:
            return
        
        flags_str = match.group(1) or ""
        var_name = match.group(2)
        
        var = Variable()
        var.name = var_name
        
        # Parse flags
        if 'i' in flags_str.lower():
            var.flags = 1  # Import
        if 'e' in flags_str.lower():
            var.flags |= 2  # Export
        if 'l' in flags_str.lower():
            var.flags = 3  # Local
        if 'g' in flags_str.lower():
            var.flags = 4  # Global
        
        self._current_dialogue.variables.append(var)
        self._current_dialogue.varcnt += 1
    
    def _handle_timed_event(self, line: str, result: ImportResult):
        """Handle timed event definition"""
        match = re.match(r'timedevent\s+(\w+)\s*;?', line, re.IGNORECASE)
        if not match:
            return
        
        event = TimeEvent()
        event.fixedparamname = match.group(1)
        
        self._current_dialogue.timedevents.append(event)
        self._current_dialogue.timedeventcnt += 1
    
    def _handle_float_node(self, line: str, result: ImportResult):
        """Handle float node definition"""
        match = re.match(r'floatnode\s+(\w+)\s*;?', line, re.IGNORECASE)
        if not match:
            return
        
        node = FloatNode()
        node.nodename = match.group(1)
        
        self._current_dialogue.floatnodes.append(node)
        self._current_dialogue.floatnodecount += 1
        self._context.current_float_node = node
    
    def _handle_node_property(self, line: str, result: ImportResult):
        """Handle node property assignment"""
        if not self._context.current_node:
            return
        
        match = re.match(r'(\w+)\s*=\s*(.+)$', line)
        if not match:
            return
        
        prop_name = match.group(1).lower()
        prop_value = match.group(2).strip().strip('"')
        
        if prop_name == 'text':
            self._context.current_node.npctext = prop_value
        elif prop_name == 'text_female':
            self._context.current_node.npctext_female = prop_value
        elif prop_name == 'notes':
            self._context.current_node.notes = prop_value
