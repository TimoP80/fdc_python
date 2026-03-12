"""
DDF (Dialogue Definition Format) Output Module

Provides functionality to export FMF dialogues to DDF format for use with
the FMFC commandline compiler and GUI dialogue converter.

Based on the original Delphi ddf_output.pas implementation
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from models.dialogue import (
    Dialogue, DialogueNode, PlayerOption, Condition,
    SkillCheck, FloatNode, TimeEvent, Variable,
    StartingCondition, CustomProcedure, CheckType, CompareType
)

logger = logging.getLogger(__name__)

# Constants matching Pascal implementation
VAR_FLAGS_NONE = 0
VAR_FLAGS_IMPORT = 1
VAR_FLAGS_EXPORT = 2
VAR_FLAGS_LOCAL = 3

VAR_TYPE_STRING = 0
VAR_TYPE_INT = 1
VAR_TYPE_FLOAT = 2

# Check field constants
CHECK_FIELD_SKILL_SMALLGUNS = 0
CHECK_FIELD_SKILL_BIGGUNS = 1
CHECK_FIELD_SKILL_ENERGYWEAPONS = 2
CHECK_FIELD_SKILL_UNARMED = 3
CHECK_FIELD_SKILL_MELEE = 4
CHECK_FIELD_SKILL_THROWING = 5
CHECK_FIELD_SKILL_FIRSTAID = 6
CHECK_FIELD_SKILL_DOCTOR = 7
CHECK_FIELD_SKILL_SNEAK = 8
CHECK_FIELD_SKILL_LOCKPICK = 9
CHECK_FIELD_SKILL_STEAL = 10
CHECK_FIELD_SKILL_TRAPS = 11
CHECK_FIELD_SKILL_SCIENCE = 12
CHECK_FIELD_SKILL_REPAIR = 13
CHECK_FIELD_SKILL_SPEECH = 14
CHECK_FIELD_SKILL_BARTER = 15
CHECK_FIELD_SKILL_GAMBLING = 16
CHECK_FIELD_SKILL_OUTDOORSMAN = 17

CHECK_FIELD_STAT_ST = 0
CHECK_FIELD_STAT_PE = 1
CHECK_FIELD_STAT_EN = 2
CHECK_FIELD_STAT_CH = 3
CHECK_FIELD_STAT_IN = 4
CHECK_FIELD_STAT_AG = 5
CHECK_FIELD_STAT_LK = 6


class DDFOutputConfig:
    """Configuration for DDF output"""
    
    def __init__(self):
        self.ssl_path: str = ""
        self.msg_path: str = ""
        self.template_name: str = ""
        self.template_path: str = ""
        self.msg_step: int = 200  # Default line number step for messages


class DDFExporter:
    """
    Exports FMF dialogues to DDF format
    
    DDF (Dialogue Definition Format) is an intermediate format used by
    the Fallout dialogue compiler tools.
    """
    
    def __init__(self, config: Optional[DDFOutputConfig] = None):
        self.config = config or DDFOutputConfig()
        self.current_dialogue: Optional[Dialogue] = None
        
    def export_to_ddf(self, dialogue: Dialogue) -> List[str]:
        """
        Export a dialogue to DDF format
        
        Args:
            dialogue: The Dialogue object to export
            
        Returns:
            List of strings representing the DDF output
        """
        self.current_dialogue = dialogue
        output_lines: List[str] = []
        
        # Add header comment
        output_lines.extend(self._generate_header())
        
        # Add output file names
        output_lines.extend(self._generate_output_paths())
        
        # Add script metadata
        output_lines.extend(self._generate_metadata())
        
        # Add description procedure
        output_lines.extend(self._generate_description_proc())
        
        # Add start nodes
        output_lines.extend(self._generate_start_nodes())
        
        # Add variable definitions
        output_lines.extend(self._generate_variables())
        
        # Add timed events
        output_lines.extend(self._generate_timed_events())
        
        # Add dialogue nodes
        output_lines.extend(self._generate_dialogue_nodes())
        
        return output_lines
    
    def _generate_header(self) -> List[str]:
        """Generate the DDF file header comment"""
        lines = [
            "/*",
            "",
            " Intermediate DDF File",
            " Exported by Fallout Dialogue Creator",
            "",
            f"NPC: {self.current_dialogue.npcname or 'Unknown'}",
            f"Location: {self.current_dialogue.location or 'Unknown'}",
            f"Description: {self.current_dialogue.description or 'None'}",
            "",
            "*/",
            ""
        ]
        return lines
    
    def _generate_output_paths(self) -> List[str]:
        """Generate output file path declarations"""
        filename = Path(self.current_dialogue.filename or "dialogue").stem
        ssl_file = f"{self.config.ssl_path}/{filename}.ssl" if self.config.ssl_path else f"{filename}.ssl"
        msg_file = f"{self.config.msg_path}/{filename}.msg" if self.config.msg_path else f"{filename}.msg"
        
        lines = [
            f'MSGOutputName = "{msg_file}"',
            f'SCROutputName = "{ssl_file}"',
            f'ScriptTemplate = "{self.config.template_path or ""}"',
            f'ScriptID = {self._generate_script_id()}',
            ""
        ]
        return lines
    
    def _generate_script_id(self) -> str:
        """Generate script ID from filename"""
        filename = Path(self.current_dialogue.filename or "dialogue").stem
        # Convert to uppercase and replace spaces with underscores
        return filename.upper().replace(" ", "_")
    
    def _generate_metadata(self) -> List[str]:
        """Generate NPC metadata"""
        lines = [
            f'NPCName = "{self._escape_string(self.current_dialogue.npcname or "")}"',
            f'Description = "{self._escape_string(self.current_dialogue.description or "")}"',
            f'Location = "{self._escape_string(self.current_dialogue.location or "")}"',
            ""
        ]
        return lines
    
    def _generate_description_proc(self) -> List[str]:
        """Generate the description procedure"""
        lines = [
            "descproc",
            "begin;",
            f'unknown = "{self._escape_string(self.current_dialogue.unknowndesc or "")}"',
            f'known = "{self._escape_string(self.current_dialogue.knowndesc or "")}"',
            f'detailed = "{self._escape_string(self.current_dialogue.detaileddesc or "")}"',
            "end;",
            ""
        ]
        return lines
    
    def _generate_start_nodes(self) -> List[str]:
        """Generate start node definitions"""
        lines = ["StartNodes", "Begin"]
        
        if self.current_dialogue.startconditioncnt == 0:
            # No conditions, use default
            if self.current_dialogue.nodecount > 0:
                default_node = self.current_dialogue.nodes[0].nodename
            elif self.current_dialogue.floatnodecount > 0:
                default_node = self.current_dialogue.floatnodes[0].nodename
            else:
                default_node = "node_not_found"
            
            lines.append(f"Case (default): {default_node} EndCase")
        else:
            # Has starting conditions
            for i, start_cond in enumerate(self.current_dialogue.startconditions):
                if i != self.current_dialogue.default_cond:
                    condition_str = self._get_condition_str(start_cond)
                    lines.append(f"Case {condition_str}: {start_cond.goto_node} EndCase")
            
            # Default case
            if self.current_dialogue.default_cond != -1:
                default_cond = self.current_dialogue.startconditions[self.current_dialogue.default_cond]
                lines.append(f"Case (default): {default_cond.goto_node} EndCase")
        
        lines.append("End")
        lines.append("")
        
        return lines
    
    def _get_condition_str(self, start_cond: StartingCondition) -> str:
        """Convert starting conditions to condition string"""
        result = ""
        
        for i, cond in enumerate(start_cond.conditions):
            result += f"({cond.resolved_code})"
            if i < len(start_cond.conditions) - 1:
                if cond.link.value == 1:  # AND
                    result += " and "
                elif cond.link.value == 2:  # OR
                    result += " or "
        
        return result
    
    def _generate_variables(self) -> List[str]:
        """Generate variable definitions"""
        lines = []
        
        if self.current_dialogue.varcnt > 0:
            lines.append("/* Variable definitions */")
            
            for var in self.current_dialogue.variables:
                varflags = self._get_var_flags_str(var.flags)
                notes = self._get_var_notes(var)
                value_str = self._get_var_value_str(var)
                
                if var.vartype != -1:
                    lines.append(f"variable{varflags}{var.name}{notes} = {value_str};")
                else:
                    lines.append(f"variable{varflags}{var.name}{notes};")
            
            lines.append("")
        
        return lines
    
    def _get_var_flags_str(self, flags: int) -> str:
        """Get variable flags as string"""
        flags_map = {
            VAR_FLAGS_NONE: " ",
            VAR_FLAGS_IMPORT: " import ",
            VAR_FLAGS_EXPORT: " export ",
            VAR_FLAGS_LOCAL: " local "
        }
        return flags_map.get(flags, " ")
    
    def _get_var_notes(self, var: Variable) -> str:
        """Get variable notes formatted for DDF"""
        if not var.notes:
            return ""
        
        notes = var.notes.replace("\r\n", "\\n").replace("\n", "\\n").replace("\t", "\\t").replace('"', '\\"')
        return f' notes "{notes}"'
    
    def _get_var_value_str(self, var: Variable) -> str:
        """Get variable value as string"""
        if var.value is None:
            return "0"
        
        if var.vartype == VAR_TYPE_STRING:
            return f'"{var.value}"'
        elif var.vartype == VAR_TYPE_FLOAT:
            return str(float(var.value))
        else:
            return str(var.value)
    
    def _generate_timed_events(self) -> List[str]:
        """Generate timed event definitions"""
        lines = []
        
        if self.current_dialogue.timedeventcnt > 0:
            lines.append("timed_events_block")
            lines.append(f"default_event={self.current_dialogue.start_time_event};")
            lines.append("begin")
            
            for event in self.current_dialogue.timedevents:
                lines.append(f"    time_event {event.fixedparamname}={event.fixedparamenumindex};")
                
                if not event.israndom:
                    lines.append(f"    interval {event.interval};")
                else:
                    lines.append(f"    interval {event.mininterval} - {event.maxinterval};")
                
                lines.append("    code")
                lines.append("       begin")
                
                for i, action in enumerate(event.actionlines):
                    line_data = action.linedata.replace('"', '\\"')
                    if i < len(event.actionlines) - 1:
                        lines.append(f'      "{line_data}",')
                    else:
                        lines.append(f'      "{line_data}"')
                
                lines.append("        end")
            
            lines.append("  end")
            lines.append("")
        
        return lines
    
    def _generate_dialogue_nodes(self) -> List[str]:
        """Generate all dialogue nodes"""
        lines = ["dialogue:", "begin"]
        
        line_base = 200
        
        # First, generate float nodes
        for float_node in self.current_dialogue.floatnodes:
            lines.extend(self._generate_float_node(float_node, line_base))
            line_base += self._calculate_line_increment(float_node.messagecnt)
        
        # Then generate regular nodes
        for node in self.current_dialogue.nodes:
            lines.extend(self._generate_dialogue_node(node, line_base))
            line_base += self._calculate_node_line_increment(node)
        
        lines.append("end")
        
        return lines
    
    def _generate_float_node(self, float_node: FloatNode, line_base: int) -> List[str]:
        """Generate a float node"""
        lines = []
        
        if float_node.notes:
            notes = float_node.notes.replace("\r\n", "\\n").replace("\n", "\\n").replace('"', '\\"')
            lines.append(f"  {float_node.nodename}: (\"{float_node.notes}\") notes \"{notes}\"")
        else:
            lines.append(f"  {float_node.nodename}: ")
        
        lines.append(f"  StartNum={line_base};")
        lines.append("")
        lines.append("   begin")
        lines.append("    RandomFloats")
        lines.append("    (")
        
        for i, message in enumerate(float_node.messages):
            msg = message.replace('"', '\\"')
            if i < len(float_node.messages) - 1:
                lines.append(f'    "{msg}",')
            else:
                lines.append(f'    "{msg}"')
        
        lines.append("    )")
        lines.append("   end")
        lines.append("")
        
        return lines
    
    def _generate_dialogue_node(self, node: DialogueNode, line_base: int) -> List[str]:
        """Generate a single dialogue node"""
        lines = []
        
        # Node header with notes
        if node.notes:
            notes = node.notes.replace("\r\n", "\\n").replace("\n", "\\n").replace('"', '\\"')
            lines.append(f"     {node.nodename}: notes \"{notes}\"")
        else:
            lines.append(f"     {node.nodename}: ")
        
        lines.append(f"     StartNum={line_base};")
        
        # Add custom procedures associated with this node
        for proc in self.current_dialogue.customprocs:
            if proc.associatewithnode == self.current_dialogue.nodes.index(node):
                lines.extend(self._generate_custom_proc(proc))
        
        lines.append("    begin")
        
        # Add skill checks
        for skill_check in node.skillchecks:
            lines.extend(self._generate_skill_check(skill_check))
        
        # Add NPC text
        if node.npctext:
            npc_text = node.npctext.replace('"', '\\"')
            lines.append(f'       reply("{npc_text}")')
        
        if node.npctext_female:
            npc_text_female = node.npctext_female.replace('"', '\\"')
            lines.append(f'       reply_female("{npc_text_female}")')
        
        # Add player options
        for option in node.options:
            lines.extend(self._generate_player_option(option))
        
        lines.append("    end")
        lines.append("")
        
        return lines
    
    def _generate_custom_proc(self, proc: CustomProcedure) -> List[str]:
        """Generate custom procedure"""
        lines = [f"add_new_proc {proc.name} {{"]
        
        code_lines = proc.lines.split('\n')
        for i, line in enumerate(code_lines):
            line = line.replace('"', '\\"')
            if i < len(code_lines) - 1:
                lines.append(f'  "{line}",')
            else:
                lines.append(f'  "{line}"')
        
        lines.append("}")
        
        return lines
    
    def _generate_skill_check(self, skill_check: SkillCheck) -> List[str]:
        """Generate skill check definition"""
        lines = [
            f"addskillcheck {skill_check.check_proc_name} {{",
            f"field = {self._skill_field_to_const(skill_check.check_what)}",
            f"modifier = {skill_check.modifier}"
        ]
        
        # Success and failure nodes
        if skill_check.successnode:
            lines.append(f"success_node = {skill_check.successnode}")
        if skill_check.failurenode:
            lines.append(f"failure_node = {skill_check.failurenode}")
        
        lines.append("}")
        
        return lines
    
    def _skill_field_to_const(self, fld: int) -> str:
        """Convert skill field to constant name"""
        skill_fields = {
            CHECK_FIELD_SKILL_SMALLGUNS: "CHECK_FIELD_SKILL_SMALLGUNS",
            CHECK_FIELD_SKILL_BIGGUNS: "CHECK_FIELD_SKILL_BIGGUNS",
            CHECK_FIELD_SKILL_ENERGYWEAPONS: "CHECK_FIELD_SKILL_ENERGYWEAPONS",
            CHECK_FIELD_SKILL_UNARMED: "CHECK_FIELD_SKILL_UNARMED",
            CHECK_FIELD_SKILL_MELEE: "CHECK_FIELD_SKILL_MELEE",
            CHECK_FIELD_SKILL_THROWING: "CHECK_FIELD_SKILL_THROWING",
            CHECK_FIELD_SKILL_FIRSTAID: "CHECK_FIELD_SKILL_FIRSTAID",
            CHECK_FIELD_SKILL_DOCTOR: "CHECK_FIELD_SKILL_DOCTOR",
            CHECK_FIELD_SKILL_SNEAK: "CHECK_FIELD_SKILL_SNEAK",
            CHECK_FIELD_SKILL_LOCKPICK: "CHECK_FIELD_SKILL_LOCKPICK",
            CHECK_FIELD_SKILL_STEAL: "CHECK_FIELD_SKILL_STEAL",
            CHECK_FIELD_SKILL_TRAPS: "CHECK_FIELD_SKILL_TRAPS",
            CHECK_FIELD_SKILL_SCIENCE: "CHECK_FIELD_SKILL_SCIENCE",
            CHECK_FIELD_SKILL_REPAIR: "CHECK_FIELD_SKILL_REPAIR",
            CHECK_FIELD_SKILL_SPEECH: "CHECK_FIELD_SKILL_SPEECH",
            CHECK_FIELD_SKILL_BARTER: "CHECK_FIELD_SKILL_BARTER",
            CHECK_FIELD_SKILL_GAMBLING: "CHECK_FIELD_SKILL_GAMBLING",
            CHECK_FIELD_SKILL_OUTDOORSMAN: "CHECK_FIELD_SKILL_OUTDOORSMAN",
        }
        
        stat_base = 18
        if fld >= stat_base:
            stat_fields = {
                stat_base + CHECK_FIELD_STAT_ST: "CHECK_FIELD_STAT_STRENGTH",
                stat_base + CHECK_FIELD_STAT_PE: "CHECK_FIELD_STAT_PERCEPTION",
                stat_base + CHECK_FIELD_STAT_EN: "CHECK_FIELD_STAT_ENDURANCE",
                stat_base + CHECK_FIELD_STAT_CH: "CHECK_FIELD_STAT_CHARISMA",
                stat_base + CHECK_FIELD_STAT_IN: "CHECK_FIELD_STAT_INTELLIGENCE",
                stat_base + CHECK_FIELD_STAT_AG: "CHECK_FIELD_STAT_AGILITY",
                stat_base + CHECK_FIELD_STAT_LK: "CHECK_FIELD_STAT_LUCK",
            }
            return stat_fields.get(fld, f"UNKNOWN_FIELD_{fld}")
        
        return skill_fields.get(fld, f"UNKNOWN_FIELD_{fld}")
    
    def _generate_player_option(self, option: PlayerOption) -> List[str]:
        """Generate player option"""
        lines = []
        
        option_text = option.optiontext.replace('"', '\\"')
        
        # Build option flags
        flags = []
        if option.reaction.value == 1:  # GOOD
            flags.append("good")
        elif option.reaction.value == 2:  # BAD
            flags.append("bad")
        
        if option.genderflags.value == 1:  # MALE
            flags.append("male")
        elif option.genderflags.value == 2:  # FEMALE
            flags.append("female")
        
        flags_str = f" [{', '.join(flags)}]" if flags else ""
        
        # Generate option with conditions if present
        if option.conditions and option.conditioncnt > 0:
            for cond in option.conditions:
                cond_code = cond.resolved_code or ""
                lines.append(f'       choice({option.intcheck}, "{option_text}", {option.nodelink}) if ({cond_code}){flags_str}')
        else:
            lines.append(f'       choice({option.intcheck}, "{option_text}", {option.nodelink}){flags_str}')
        
        return lines
    
    def _calculate_line_increment(self, message_count: int) -> int:
        """Calculate line number increment for float node"""
        if message_count > self.config.msg_step:
            return message_count
        return self.config.msg_step
    
    def _calculate_node_line_increment(self, node: DialogueNode) -> int:
        """Calculate line number increment for dialogue node"""
        # Each node needs at least 2 lines (reply + choice)
        return max(2, len(node.options) + 1)
    
    def _escape_string(self, text: str) -> str:
        """Escape special characters in strings"""
        if not text:
            return ""
        return text.replace("\r\n", "\\n").replace("\n", "\\n").replace("\t", "\\t").replace('"', '\\"')
    
    def save_to_file(self, dialogue: Dialogue, file_path: Path) -> None:
        """
        Export dialogue to DDF file
        
        Args:
            dialogue: The Dialogue object to export
            file_path: Path to save the DDF file
        """
        output_lines = self.export_to_ddf(dialogue)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        logger.info(f"Exported dialogue to DDF: {file_path}")


def export_dialogue_to_ddf(dialogue: Dialogue, output_path: Path, 
                          ssl_path: str = "", msg_path: str = "",
                          template_path: str = "") -> bool:
    """
    Convenience function to export a dialogue to DDF format
    
    Args:
        dialogue: The Dialogue object to export
        output_path: Path for the output DDF file
        ssl_path: Path for SSL output
        msg_path: Path for MSG output
        template_path: Path to script template
        
    Returns:
        True if export was successful
    """
    try:
        config = DDFOutputConfig()
        config.ssl_path = ssl_path
        config.msg_path = msg_path
        config.template_path = template_path
        
        exporter = DDFExporter(config)
        exporter.save_to_file(dialogue, output_path)
        
        return True
    except Exception as e:
        logger.error(f"Failed to export dialogue to DDF: {e}")
        return False
