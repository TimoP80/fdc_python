"""
SSL (Fallout Scripting Language) Exporter for Fallout Dialogue Creator

Generates proper Fallout 2 compatible SSL script files with:
- Complete dialogue structure with speaker IDs
- Response text with condition checks
- Procedure calls for node transitions
- Skill check integration
- Fallout 1 and Fallout 2 specific formats

Supports both Fallout 1 and Fallout 2 export formats with proper encoding.
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from models.dialogue import (
    Dialogue, DialogueNode, PlayerOption, Condition, 
    CheckType, CompareType, LinkType, SkillCheck, CustomProcedure,
    Variable, Gender, Reaction
)

logger = logging.getLogger(__name__)


class GameVersion(Enum):
    """Target game version for export"""
    FALLOUT_1 = "fallout1"
    FALLOUT_2 = "fallout2"


# Default header paths for Fallout 1 and Fallout 2
FALLOUT_2_DEFAULT_HEADERS = Path(r"C:\Games\Fallout2\maps\scripts\headers")
FALLOUT_1_DEFAULT_HEADERS = Path(r"C:\Games\Fallout\maps\scripts\headers")


@dataclass
class ScriptHeaderConfig:
    """
    Configuration for Fallout 2 script header files.
    
    Allows users to specify the location of header files (.h) needed
    for SSL script compilation and validation.
    """
    
    # Primary header search path
    headers_path: Path = field(default_factory=lambda: Path("headers"))
    
    # Additional fallback paths
    fallback_paths: List[Path] = field(default_factory=list)
    
    # Game version for default paths
    game_version: GameVersion = GameVersion.FALLOUT_2
    
    # Whether to validate headers exist
    validate_on_use: bool = True
    
    def __post_init__(self):
        """Validate and normalize paths after initialization"""
        # Convert string paths to Path objects
        if isinstance(self.headers_path, str):
            self.headers_path = Path(self.headers_path)
        
        self.fallback_paths = [
            Path(p) if isinstance(p, str) else p 
            for p in self.fallback_paths
        ]
    
    @property
    def all_paths(self) -> List[Path]:
        """Get all header search paths including fallbacks"""
        paths = [self.headers_path] + self.fallback_paths
        return [p for p in paths if p]
    
    def find_header(self, header_name: str) -> Optional[Path]:
        """
        Find a header file in any of the search paths.
        
        Args:
            header_name: Name of the header file (e.g., "define.h")
            
        Returns:
            Path to the header file if found, None otherwise
        """
        for search_path in self.all_paths:
            header_path = search_path / header_name
            if header_path.exists() and header_path.is_file():
                logger.debug(f"Found header {header_name} at {header_path}")
                return header_path
        
        logger.warning(f"Header file not found: {header_name}")
        return None
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate that required headers exist.
        
        Returns:
            Tuple of (is_valid, list of missing headers)
        """
        required_headers = ["define.h", "command.h"]
        missing = []
        
        for header in required_headers:
            if not self.find_header(header):
                missing.append(header)
        
        is_valid = len(missing) == 0
        return is_valid, missing
    
    @classmethod
    def from_settings(cls, settings) -> 'ScriptHeaderConfig':
        """
        Create configuration from application settings.
        
        Args:
            settings: Application Settings object
            
        Returns:
            ScriptHeaderConfig with values from settings
        """
        from core.settings import Settings
        
        if not isinstance(settings, Settings):
            settings = Settings()
        
        # Get configured paths
        headers_path = settings.get('headers_path', 'headers')
        fo2_path = settings.get('fo2_data_path', '')
        
        # Build fallback paths
        fallbacks = []
        if fo2_path:
            fo2_headers = Path(fo2_path) / "maps" / "scripts" / "headers"
            if fo2_headers.exists():
                fallbacks.append(fo2_headers)
        
        # Add default paths based on game version
        fallbacks.append(FALLOUT_2_DEFAULT_HEADERS)
        fallbacks.append(FALLOUT_1_DEFAULT_HEADERS)
        
        return cls(
            headers_path=Path(headers_path),
            fallback_paths=fallbacks,
            game_version=GameVersion.FALLOUT_2
        )
    
    @classmethod
    def with_defaults(cls, game_version: GameVersion = GameVersion.FALLOUT_2) -> 'ScriptHeaderConfig':
        """
        Create configuration with default paths for the specified game version.
        
        Args:
            game_version: Target game version
            
        Returns:
            ScriptHeaderConfig with default paths
        """
        if game_version == GameVersion.FALLOUT_1:
            default_path = FALLOUT_1_DEFAULT_HEADERS
        else:
            default_path = FALLOUT_2_DEFAULT_HEADERS
        
        return cls(
            headers_path=default_path,
            fallback_paths=[FALLOUT_2_DEFAULT_HEADERS, FALLOUT_1_DEFAULT_HEADERS],
            game_version=game_version
        )


@dataclass
class ExportConfig:
    """Configuration for SSL export"""
    game_version: GameVersion = GameVersion.FALLOUT_2
    output_directory: Path = Path("output")
    script_number: str = "001"
    headers_path: str = "headers"
    # New header configuration
    header_config: Optional[ScriptHeaderConfig] = None
    include_debug_comments: bool = True
    generate_starting_conditions: bool = True
    generate_skill_checks: bool = True
    use_fallout1_compatibility: bool = False
    encoding: str = "cp1252"  # Fallout 2 default encoding
    
    def __post_init__(self):
        """Initialize header config if not provided"""
        if self.header_config is None:
            # Create default header config based on game version
            self.header_config = ScriptHeaderConfig.with_defaults(self.game_version)
    
    def get_header_config(self) -> ScriptHeaderConfig:
        """Get the header configuration, creating one if needed"""
        if self.header_config is None:
            self.header_config = ScriptHeaderConfig.with_defaults(self.game_version)
        return self.header_config
    
    def get_headers_path_string(self) -> str:
        """Get headers path as string for backward compatibility"""
        return self.get_header_config().headers_path


class ConditionGenerator:
    """Generates SSL condition code from Condition objects"""
    
    # Mapping of CheckType to SSL function
    STAT_FUNCTIONS = {
        0: "getStrength",
        1: "getPerception", 
        2: "getEndurance",
        3: "getCharisma",
        4: "getIntelligence",
        5: "getAgility",
        6: "getLuck",
    }
    
    SKILL_FUNCTIONS = {
        0: "skill_level",
        1: "skill_level",
        2: "skill_level",
        # ... more skill mappings
    }
    
    @staticmethod
    def generate_condition_code(condition: Condition) -> str:
        """Generate SSL code for a condition check"""
        code_parts = []
        
        # Handle different check types
        if condition.check_type == CheckType.STAT:
            stat_func = ConditionGenerator.STAT_FUNCTIONS.get(
                condition.check_field, "getStrength"
            )
            code = f"{stat_func}(dude_obj)"
            code_parts.append(ConditionGenerator._apply_comparison(
                code, condition.check_eval, condition.check_value
            ))
            
        elif condition.check_type == CheckType.SKILL:
            skill_id = condition.check_field
            code = f"skill_level(dude_obj, {skill_id}, 0)"
            code_parts.append(ConditionGenerator._apply_comparison(
                code, condition.check_eval, condition.check_value
            ))
            
        elif condition.check_type == CheckType.GLOBAL_VAR:
            code = f"global_var({condition.check_field})"
            code_parts.append(ConditionGenerator._apply_comparison(
                code, condition.check_eval, condition.check_value
            ))
            
        elif condition.check_type == CheckType.LOCAL_VAR:
            code = f"local_var({condition.check_field})"
            code_parts.append(ConditionGenerator._apply_comparison(
                code, condition.check_eval, condition.check_value
            ))
            
        elif condition.check_type == CheckType.MONEY:
            code = "item_caps_total(dude_obj)"
            code_parts.append(ConditionGenerator._apply_comparison(
                code, condition.check_eval, condition.check_value
            ))
            
        elif condition.check_type == CheckType.CUSTOM_CODE:
            code_parts.append(condition.resolved_code or condition.var_ptr)
        
        return code_parts[0] if code_parts else "1"  # Default to true
    
    @staticmethod
    def _apply_comparison(var_code: str, compare_type: CompareType, value: str) -> str:
        """Apply comparison operator to variable code"""
        # Normalize value
        value = str(value).strip()
        
        if compare_type == CompareType.EQUAL:
            return f"({var_code} == {value})"
        elif compare_type == CompareType.NOT_EQUAL:
            return f"({var_code} != {value})"
        elif compare_type == CompareType.LARGER_THAN:
            return f"({var_code} > {value})"
        elif compare_type == CompareType.LESS_THAN:
            return f"({var_code} < {value})"
        elif compare_type == CompareType.LARGER_EQUAL:
            return f"({var_code} >= {value})"
        elif compare_type == CompareType.LESS_EQUAL:
            return f"({var_code} <= {value})"
        else:
            return f"({var_code} == {value})"
    
    @staticmethod
    def generate_option_conditions(options: List[PlayerOption]) -> List[str]:
        """Generate condition code for player options"""
        conditions = []
        
        for option in options:
            if option.conditions:
                # Generate combined condition
                code_parts = []
                for i, cond in enumerate(option.conditions):
                    cond_code = ConditionGenerator.generate_condition_code(cond)
                    code_parts.append(cond_code)
                
                if code_parts:
                    # Join with AND/OR based on link type
                    link = option.conditions[0].link if option.conditions else LinkType.AND
                    if link == LinkType.AND:
                        combined = " and ".join(f"({c})" for c in code_parts)
                    else:
                        combined = " or ".join(f"({c})" for c in code_parts)
                    conditions.append(combined)
                else:
                    conditions.append("1")
            else:
                conditions.append("1")
        
        return conditions


class SSLExporter:
    """Main SSL exporter class"""
    
    # Standard procedure names used in Fallout 2
    STANDARD_PROCEDURES = [
        "start", "critter_p_proc", "pickup_p_proc", "talk_p_proc",
        "destroy_p_proc", "look_at_p_proc", "description_p_proc",
        "use_skill_on_p_proc", "damage_p_proc", "map_enter_p_proc",
        "timed_event_p_proc", "Node998", "Node999"
    ]
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
        self.msg_id_counter = 100  # Starting MSG ID
    
    def export(self, dialogue: Dialogue, output_path: Optional[Path] = None) -> str:
        """
        Export dialogue to SSL format.
        
        Args:
            dialogue: Dialogue object to export
            output_path: Optional output file path
            
        Returns:
            Generated SSL content as string
        """
        logger.info(f"Exporting SSL for dialogue: {dialogue.npcname}")
        
        # Generate the SSL content
        ssl_content = self._generate_ssl(dialogue)
        
        # Write to file if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use appropriate encoding
            encoding = self.config.encoding if self.config.encoding else "utf-8"
            output_path.write_text(ssl_content, encoding=encoding)
            logger.info(f"SSL exported to: {output_path}")
        
        return ssl_content
    
    def _generate_ssl(self, dialogue: Dialogue) -> str:
        """Generate complete SSL content"""
        
        # Build sections
        header = self._generate_header(dialogue)
        variables = self._generate_variables(dialogue)
        procedure_declarations = self._generate_procedure_declarations(dialogue)
        main_procedures = self._generate_main_procedures(dialogue)
        node_procedures = self._generate_node_procedures(dialogue)
        skill_check_procedures = self._generate_skill_check_procedures(dialogue)
        custom_procedures = self._generate_custom_procedures(dialogue)
        
        return f"""{header}

{variables}

{procedure_declarations}

{main_procedures}

{node_procedures}

{skill_check_procedures}

{custom_procedures}
"""
    
    def _generate_header(self, dialogue: Dialogue) -> str:
        """Generate SSL file header with metadata"""
        from datetime import datetime
        
        game_name = "Fallout 1" if self.config.game_version == GameVersion.FALLOUT_1 else "Fallout 2"
        
        header = f"""/*
    Name:           {dialogue.npcname}
    Location:       {dialogue.location or 'Unknown'}
    Description:    {dialogue.description or 'Dialogue script'}

    Created:        {datetime.now().strftime('%Y-%m-%d')}
    Game Version:   {game_name}
    Script Number:  {self.config.script_number}
*/

/* Include Files */

#define NPC_REACTION_VAR        7

#include "{self.config.headers_path}\\\\define.h"
#include "{self.config.headers_path}\\\\command.h"
#include "{self.config.headers_path}\\\\ModReact.h"

/* Script Number */
#define NAME                    SCRIPT_{self.config.script_number}

/* Helper Variables */
variable Evil_Critter:=0;
variable Slavery_Tolerant:=SLAVE_TOLERANT;
variable Karma_Perception:=KARMA_PERCEPTION1;
variable temp;
"""
        
        if self.config.use_fallout1_compatibility:
            header = header.replace('#include "', '#include "..\\\\')
        
        return header
    
    def _generate_variables(self, dialogue: Dialogue) -> str:
        """Generate variable declarations"""
        
        # Standard local variables (saved)
        standard_vars = """/* Local Variables which are saved */
#define LVAR_Herebefore                 (4)
#define LVAR_Hostile                    (5)
#define LVAR_Personal_Enemy             (6)
#define LVAR_Caught_Thief               (7)"""
        
        # User-defined variables
        user_vars = []
        for var in dialogue.variables:
            user_vars.append(f"#define LVAR_{var.name.upper()} ({var.value})")
        
        # Non-saved local variables
        non_saved_vars = """
/* Local variables which do not need to be saved between map changes */
variable Only_Once:=0;
variable global_temp:=0;"""
        
        return f"{standard_vars}\n\n{chr(10).join(user_vars)}\n{non_saved_vars}"
    
    def _generate_procedure_declarations(self, dialogue: Dialogue) -> str:
        """Generate procedure declarations"""
        
        # Standard procedure declarations
        std_procs = """/* Standard Script Procedures */
procedure start;
procedure critter_p_proc;
procedure pickup_p_proc;
procedure talk_p_proc;
procedure destroy_p_proc;
procedure look_at_p_proc;
procedure description_p_proc;
procedure use_skill_on_p_proc;
procedure damage_p_proc;
procedure map_enter_p_proc;
procedure timed_event_p_proc;

/* Node Procedures */
procedure Node998;                                      // Combat
procedure Node999;                                      // Ending"""

        # Node procedure declarations
        node_decls = []
        for i, node in enumerate(dialogue.nodes):
            node_name = node.nodename or f"Node{i}"
            node_decls.append(f"procedure {node_name};")
        
        # Skill check procedure declarations
        skill_decls = []
        if self.config.generate_skill_checks:
            for node in dialogue.nodes:
                for sc in node.skillchecks:
                    if sc.check_proc_name:
                        skill_decls.append(f"procedure {sc.check_proc_name};")
        
        # Custom procedure declarations
        custom_decls = []
        for proc in dialogue.customprocs:
            custom_decls.append(f"procedure {proc.name};")
        
        all_decls = node_decls + skill_decls + custom_decls
        
        return f"{std_procs}\n\n/* Script Specific Procedures */\n" + "\n".join(all_decls)
    
    def _generate_main_procedures(self, dialogue: Dialogue) -> str:
        """Generate standard main procedures"""
        
        return """procedure start begin
end

procedure map_enter_p_proc begin
   Only_Once:=0;
end

procedure critter_p_proc begin
   if ((local_var(LVAR_Hostile) != 0) and (obj_can_see_obj(self_obj,dude_obj))) then begin
       set_local_var(LVAR_Hostile,1);
       self_attack_dude;
   end
end

procedure damage_p_proc begin
   if (obj_in_party(source_obj)) then begin
       set_local_var(LVAR_Personal_Enemy,1);
   end
end

procedure pickup_p_proc begin
   if (source_obj == dude_obj) then begin
       set_local_var(LVAR_Hostile,2);
   end
end

procedure talk_p_proc begin
   Evil_Critter:=0;
   Slavery_Tolerant:=SLAVE_TOLERANT;
   Karma_Perception:=KARMA_PERCEPTION1;

   CheckKarma;
   GetReaction;

   start_gdialog(NAME, self_obj, 4, -1, -1);
   gsay_start;
"""
    
    def _generate_node_procedures(self, dialogue: Dialogue) -> str:
        """Generate dialogue node procedures"""
        
        node_procs = []
        
        for i, node in enumerate(dialogue.nodes):
            node_name = node.nodename or f"Node{i}"
            node_proc = self._generate_single_node(node, i, dialogue)
            node_procs.append(node_proc)
        
        return "\n\n".join(node_procs)
    
    def _generate_single_node(self, node: DialogueNode, node_index: int, dialogue: Dialogue) -> str:
        """Generate a single dialogue node procedure"""
        
        # Get NPC text for this node
        npc_text = node.npctext or ""
        npc_text_female = node.npctext_female or npc_text
        
        # Generate MSG ID for this node's text
        msg_id = 100 + node_index + 3  # Start from 103
        
        # Generate NPC text lines
        lines = []
        
        # Custom code before dialog
        if node.customcode:
            lines.append(node.customcode)
        
        # Generate gsay_reply with NPC text
        if npc_text_female and npc_text_female != npc_text:
            # Both male and female text defined
            lines.append(f'gsay_reply({msg_id}, "{self._escape_string(npc_text)}", "{self._escape_string(npc_text_female)}");')
        else:
            lines.append(f'gsay_reply({msg_id}, "{self._escape_string(npc_text)}");')
        
        # Generate player options
        option_conditions = ConditionGenerator.generate_option_conditions(node.options)
        
        for j, option in enumerate(node.options):
            if option.optiontext:
                # Determine the target node
                target_node = option.nodelink or "Node999"
                
                # Check if there's a skill check
                if option.link_to_skillcheck:
                    # Use skill check procedure
                    skill_check = self._find_skill_check_for_option(node, j)
                    if skill_check:
                        lines.append(f'giq_option({option.intcheck}, 0, "{self._escape_string(option.optiontext)}", {skill_check.check_proc_name}, {self._get_reaction_code(option.reaction)});')
                    else:
                        lines.append(f'giq_option({option.intcheck}, 0, "{self._escape_string(option.optiontext)}", {target_node}, {self._get_reaction_code(option.reaction)});')
                else:
                    # Direct node link
                    lines.append(f'giq_option({option.intcheck}, 0, "{self._escape_string(option.optiontext)}", {target_node}, {self._get_reaction_code(option.reaction)});')
        
        # Add default end option
        lines.append('giq_option(-3, 0, "", Node999, NEUTRAL_REACTION);')
        
        proc_code = "\n   ".join(lines)
        
        return f"""procedure {node.nodename or f"Node{node_index}"} begin
   {proc_code}
   gsay_end;
   end_dialogue;
end"""
    
    def _find_skill_check_for_option(self, node: DialogueNode, option_index: int) -> Optional[SkillCheck]:
        """Find the skill check associated with an option"""
        if option_index < len(node.skillchecks):
            return node.skillchecks[option_index]
        return None
    
    def _get_reaction_code(self, reaction: Reaction) -> str:
        """Get the reaction constant from Reaction enum"""
        reaction_map = {
            Reaction.GOOD: "GOOD_REACTION",
            Reaction.BAD: "BAD_REACTION", 
            Reaction.NEUTRAL: "NEUTRAL_REACTION"
        }
        return reaction_map.get(reaction, "NEUTRAL_REACTION")
    
    def _generate_skill_check_procedures(self, dialogue: Dialogue) -> str:
        """Generate skill check procedures"""
        
        if not self.config.generate_skill_checks:
            return ""
        
        procedures = []
        
        for node in dialogue.nodes:
            for skill_check in node.skillchecks:
                if skill_check.check_proc_name:
                    proc = self._generate_skill_check_proc(skill_check)
                    procedures.append(proc)
        
        return "\n\n".join(procedures) if procedures else "// No skill checks defined"
    
    def _generate_skill_check_proc(self, skill_check: SkillCheck) -> str:
        """Generate a single skill check procedure"""
        
        skill_id = skill_check.check_what
        modifier = skill_check.modifier
        success_node = skill_check.successnode or "Node999"
        failure_node = skill_check.failurenode or "Node999"
        
        return f"""procedure {skill_check.check_proc_name} begin
   if (skill_level(dude_obj, {skill_id}, 0) >= {modifier}) then begin
       call {success_node};
   end else begin
       call {failure_node};
   end
end"""
    
    def _generate_custom_procedures(self, dialogue: Dialogue) -> str:
        """Generate custom procedures"""
        
        procedures = []
        
        for proc in dialogue.customprocs:
            proc_code = f"""procedure {proc.name} begin
{proc.lines}
end"""
            procedures.append(proc_code)
        
        return "\n\n".join(procedures) if procedures else "// No custom procedures"
    
    def _escape_string(self, text: str) -> str:
        """Escape special characters for SSL string literals"""
        if not text:
            return ""
        
        # Escape quotes and backslashes
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        
        # Handle special Fallout characters
        # Remove or replace characters not valid in SSL
        text = text.replace('\r\n', '\\n')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '')
        
        return text
    
    def get_msg_ids_used(self) -> List[int]:
        """Return list of MSG IDs that will be used"""
        return list(range(100, 100 + self.msg_id_counter))


class SSLValidator:
    """Validates SSL syntax before export"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, ssl_content: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate SSL content syntax.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        lines = ssl_content.split('\n')
        
        # Check for matching braces
        brace_count = 0
        paren_count = 0
        
        for i, line in enumerate(lines, 1):
            # Count braces
            brace_count += line.count('{') - line.count('}')
            paren_count += line.count('(') - line.count(')')
            
            # Check for common issues
            if '//' in line and line.strip().startswith('//'):
                continue  # Skip comment lines
                
            # Check for incomplete statements
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                # Check for potential issues
                if stripped.endswith(')') and not (';' in stripped or 'then' in stripped.lower()):
                    self.warnings.append(f"Line {i}: Possible incomplete statement")
        
        if brace_count != 0:
            self.errors.append(f"Unmatched braces: {brace_count} {'opening' if brace_count > 0 else 'closing'} brace(s)")
        
        if paren_count != 0:
            self.errors.append(f"Unmatched parentheses: {paren_count} {'opening' if paren_count > 0 else 'closing'} parenthesis(es)")
        
        is_valid = len(self.errors) == 0
        
        return is_valid, self.errors, self.warnings


def export_ssl(
    dialogue: Dialogue,
    output_path: Optional[Path] = None,
    config: Optional[ExportConfig] = None,
    validate: bool = True
) -> Tuple[bool, str, List[str], List[str]]:
    """
    Convenience function to export SSL.
    
    Args:
        dialogue: Dialogue to export
        output_path: Output file path
        config: Export configuration
        validate: Whether to validate before export
        
    Returns:
        Tuple of (success, content, errors, warnings)
    """
    exporter = SSLExporter(config)
    
    # Generate content first
    content = exporter.export(dialogue)
    
    # Validate if requested
    if validate:
        validator = SSLValidator()
        is_valid, errors, warnings = validator.validate(content)
        
        if not is_valid:
            return False, content, errors, warnings
    
    # Write to file if path provided
    if output_path:
        try:
            encoding = config.encoding if config and config.encoding else "utf-8"
            Path(output_path).write_text(content, encoding=encoding)
        except Exception as e:
            return False, content, [str(e)], []
    
    return True, content, [], []
