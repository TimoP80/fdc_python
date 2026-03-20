"""
Secure Python Scripting Engine for Fallout Dialogue Creator

Provides a sandboxed environment for executing custom dialogue scripts with:
- Restricted imports and builtins for security
- Access to dialogue context and player character data
- Safe execution with timeout and resource limits
- Error handling and validation

Usage:
    engine = ScriptingEngine()
    context = DialogueScriptContext(dialogue, player, current_node)
    result = engine.execute_script(script_code, context)
"""

import ast
import sys
import time
import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
import signal
try:
    import resource
except ImportError:
    # resource module not available on Windows
    resource = None

from models.dialogue import (
    Dialogue, DialogueNode, PlayerCharacter, PlayerOption,
    Condition, CheckType, CompareType, Reaction, Gender
)

logger = logging.getLogger(__name__)

class ScriptExecutionError(Exception):
    """Raised when script execution fails"""
    pass

class ScriptTimeoutError(ScriptExecutionError):
    """Raised when script execution times out"""
    pass

class ScriptSecurityError(ScriptExecutionError):
    """Raised when script violates security constraints"""
    pass

class ScriptResult(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SECURITY_VIOLATION = "security_violation"

@dataclass
class ScriptExecutionReport:
    """Report of script execution results"""
    result: ScriptResult
    output: Any = None
    error_message: str = ""
    execution_time: float = 0.0
    security_violations: List[str] = field(default_factory=list)

@dataclass
class DialogueScriptContext:
    """Context provided to scripts during execution"""
    dialogue: Dialogue
    player: PlayerCharacter
    current_node: Optional[DialogueNode] = None
    selected_option: Optional[PlayerOption] = None
    variables: Dict[str, Any] = field(default_factory=dict)

    def get_node_by_name(self, name: str) -> Optional[DialogueNode]:
        """Get node by name"""
        for node in self.dialogue.nodes:
            if node.nodename.lower() == name.lower():
                return node
        return None

    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get dialogue variable value"""
        return self.variables.get(name, default)

    def set_variable(self, name: str, value: Any):
        """Set dialogue variable value"""
        self.variables[name] = value

class RestrictedImporter:
    """Custom import system that restricts available modules"""

    # Allowed standard library modules (safe ones only)
    ALLOWED_MODULES = {
        'math', 'random', 'datetime', 'time', 're', 'string',
        'collections', 'itertools', 'functools', 'operator',
        'json', 'csv', 'io', 'copy', 'pprint'
    }

    # Blocked modules that could be dangerous
    BLOCKED_MODULES = {
        'os', 'sys', 'subprocess', 'shutil', 'pathlib',
        'socket', 'urllib', 'http', 'ftplib', 'smtplib',
        'sqlite3', 'dbm', 'pickle', 'shelve',
        'multiprocessing', 'threading', 'asyncio',
        'importlib', 'inspect', 'builtins'
    }

    def __init__(self):
        self.modules = {}

    def __import__(self, name, globals=None, locals=None, fromlist=(), level=0):
        # Check if module is blocked
        if name in self.BLOCKED_MODULES:
            raise ScriptSecurityError(f"Import of module '{name}' is not allowed")

        # Check if module is allowed
        if name not in self.ALLOWED_MODULES:
            raise ScriptSecurityError(f"Import of module '{name}' is not allowed")

        # Import the module safely
        try:
            return __import__(name, globals, locals, fromlist, level)
        except ImportError:
            raise ScriptSecurityError(f"Module '{name}' could not be imported")

class SafeBuiltins:
    """Restricted builtins for script execution"""

    # Safe builtins that scripts can use
    SAFE_BUILTINS = {
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
        'callable', 'chr', 'classmethod', 'complex', 'delattr', 'dict',
        'dir', 'divmod', 'enumerate', 'filter', 'float', 'format', 'frozenset',
        'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input',
        'int', 'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals',
        'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'ord',
        'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round',
        'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
        'super', 'tuple', 'type', 'vars', 'zip'
    }

    # Dangerous builtins to remove
    DANGEROUS_BUILTINS = {
        'eval', 'exec', 'compile', 'open', 'file', '__import__',
        'reload', 'raw_input', 'execfile'
    }

    @classmethod
    def get_safe_builtins(cls):
        """Get dictionary of safe builtins"""
        builtins = {}
        for name in cls.SAFE_BUILTINS:
            if hasattr(__builtins__, name):
                builtins[name] = getattr(__builtins__, name)
            elif isinstance(__builtins__, dict) and name in __builtins__:
                builtins[name] = __builtins__[name]

        # Add our restricted importer
        builtins['__import__'] = RestrictedImporter().__import__

        return builtins

class ScriptValidator:
    """Validates scripts for security violations"""

    DANGEROUS_NODES = {
        ast.Import, ast.ImportFrom,
        ast.Call  # We'll check calls separately
    }

    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', 'open', 'file', '__import__',
        'reload', 'input', 'raw_input', 'execfile'
    }

    def validate_script(self, script_code: str) -> List[str]:
        """Validate script code for security violations"""
        violations = []

        try:
            tree = ast.parse(script_code)
        except SyntaxError as e:
            violations.append(f"Syntax error: {e}")
            return violations

        for node in ast.walk(tree):
            # Check for dangerous AST nodes
            if isinstance(node, self.DANGEROUS_NODES):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in RestrictedImporter.BLOCKED_MODULES:
                            violations.append(f"Blocked import: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in RestrictedImporter.BLOCKED_MODULES:
                        violations.append(f"Blocked import from: {node.module}")

            # Check for dangerous function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.DANGEROUS_FUNCTIONS:
                        violations.append(f"Dangerous function call: {node.func.id}")
                elif isinstance(node.func, ast.Attribute):
                    # Check for methods like os.system, subprocess.call, etc.
                    if isinstance(node.func.value, ast.Name):
                        base_name = node.func.value.id
                        method_name = node.func.attr
                        dangerous_patterns = [
                            (base_name, method_name) for base_name in ['os', 'subprocess', 'sys']
                            for method_name in ['system', 'popen', 'call', 'run', 'exit']
                        ]
                        if (base_name, method_name) in dangerous_patterns:
                            violations.append(f"Dangerous method call: {base_name}.{method_name}")

        return violations

class ScriptingEngine:
    """Main scripting engine with sandboxed execution"""

    def __init__(self, timeout_seconds: float = 5.0, max_memory_mb: int = 50):
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb
        self.validator = ScriptValidator()

    def execute_script(self, script_code: str, context: DialogueScriptContext) -> ScriptExecutionReport:
        """Execute a script in a sandboxed environment"""
        start_time = time.time()

        # Validate script first
        violations = self.validator.validate_script(script_code)
        if violations:
            return ScriptExecutionReport(
                result=ScriptResult.SECURITY_VIOLATION,
                error_message="Script validation failed",
                security_violations=violations,
                execution_time=time.time() - start_time
            )

        # Prepare execution environment
        globals_dict = self._create_execution_globals(context)
        locals_dict = {}

        # Execute with timeout and resource limits
        try:
            result = self._execute_with_timeout(script_code, globals_dict, locals_dict)
            return ScriptExecutionReport(
                result=ScriptResult.SUCCESS,
                output=result,
                execution_time=time.time() - start_time
            )

        except ScriptTimeoutError:
            return ScriptExecutionReport(
                result=ScriptResult.TIMEOUT,
                error_message="Script execution timed out",
                execution_time=time.time() - start_time
            )

        except ScriptSecurityError as e:
            return ScriptExecutionReport(
                result=ScriptResult.SECURITY_VIOLATION,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ScriptExecutionReport(
                result=ScriptResult.ERROR,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    def _create_execution_globals(self, context: DialogueScriptContext) -> Dict[str, Any]:
        """Create the global namespace for script execution"""
        globals_dict = {
            '__builtins__': SafeBuiltins.get_safe_builtins(),
            'dialogue': context.dialogue,
            'player': context.player,
            'current_node': context.current_node,
            'selected_option': context.selected_option,
            'variables': context.variables,
            'get_node': context.get_node_by_name,
            'get_var': context.get_variable,
            'set_var': context.set_variable,
        }

        # Add convenience functions
        globals_dict.update({
            'log': logger.info,
            'debug': logger.debug,
            'warning': logger.warning,
            'error': logger.error,
        })

        return globals_dict

    def _execute_with_timeout(self, script_code: str, globals_dict: Dict[str, Any],
                            locals_dict: Dict[str, Any]) -> Any:
        """Execute script with timeout protection"""
        result = [None]
        exception = [None]

        def target():
            try:
                # Set resource limits if available
                if resource is not None:
                    try:
                        resource.setrlimit(resource.RLIMIT_CPU, (int(self.timeout_seconds), int(self.timeout_seconds)))
                        resource.setrlimit(resource.RLIMIT_AS, (self.max_memory_mb * 1024 * 1024, self.max_memory_mb * 1024 * 1024))
                    except (OSError, AttributeError):
                        # Resource limits not available on Windows
                        pass

                exec(script_code, globals_dict, locals_dict)
                result[0] = locals_dict.get('result', None)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(self.timeout_seconds)

        if thread.is_alive():
            # Timeout occurred
            raise ScriptTimeoutError("Script execution exceeded timeout")

        if exception[0]:
            raise exception[0]

        return result[0]

    def validate_script_syntax(self, script_code: str) -> bool:
        """Check if script has valid Python syntax"""
        try:
            ast.parse(script_code)
            return True
        except SyntaxError:
            return False

    def get_script_info(self, script_code: str) -> Dict[str, Any]:
        """Get information about a script"""
        info = {
            'valid_syntax': self.validate_script_syntax(script_code),
            'security_violations': self.validator.validate_script(script_code),
            'line_count': len(script_code.splitlines()),
            'char_count': len(script_code)
        }
    def _evaluate_conditions(self, conditions: List[Condition], player: PlayerCharacter) -> bool:
        """
        Evaluate a list of conditions against player character
        Enhanced implementation with basic condition checking
        """
        if not conditions:
            return True

        # For now, implement basic condition evaluation
        # This can be enhanced to support more complex logic
        result = True

        for condition in conditions:
            condition_result = self._evaluate_single_condition(condition, player)

            if condition.link == LinkType.OR:
                result = result or condition_result
            elif condition.link == LinkType.AND:
                result = result and condition_result
            else:  # NONE - replace result
                result = condition_result

        return result

    def _evaluate_single_condition(self, condition: Condition, player: PlayerCharacter) -> bool:
        """Evaluate a single condition"""
        try:
            if condition.check_type == CheckType.STAT:
                # Check player stats (strength, perception, etc.)
                stat_value = getattr(player, self._get_stat_name(condition.check_field), 0)
                return self._compare_values(stat_value, condition.check_eval, condition.check_value)

            elif condition.check_type == CheckType.SKILL:
                # Check player skills
                if 0 <= condition.check_field < len(player.skills):
                    skill_value = player.skills[condition.check_field].get('value', 0)
                    return self._compare_values(skill_value, condition.check_eval, condition.check_value)
                return False

            elif condition.check_type == CheckType.MONEY:
                # Check player caps
                return self._compare_values(player.dude_caps, condition.check_eval, condition.check_value)

            elif condition.check_type == CheckType.GLOBAL_VAR:
                # Check global variables (GVAR)
                try:
                    gvar_id = condition.check_field
                    # Try to get global variables from player, default to empty dict
                    global_vars = getattr(player, 'global_vars', {})
                    # Get the GVAR value, default to 0 if not found
                    gvar_value = global_vars.get(gvar_id, 0) if isinstance(global_vars, dict) else 0
                    return self._compare_values(gvar_value, condition.check_eval, condition.check_value)
                except Exception as e:
                    logger.warning(f"Error evaluating GLOBAL_VAR check: {e}")
                    return False

            elif condition.check_type == CheckType.LOCAL_VAR:
                # Check local variables (simplified)
                return True  # Placeholder

            elif condition.check_type == CheckType.SCRIPT_VAR:
                # Check script variables (simplified)
                return True  # Placeholder

            elif condition.check_type == CheckType.ITEM_PLAYER:
                # Check if player has item (simplified)
                return True  # Placeholder

            elif condition.check_type == CheckType.CUSTOM_CODE:
                # Custom code conditions would be evaluated via scripting
                return True  # Placeholder

        except Exception as e:
            logger.warning(f"Error evaluating condition {condition}: {e}")
            return False

        return True  # Default to true for unknown conditions

    def _get_stat_name(self, field_index: int) -> str:
        """Get stat name from field index"""
        stat_names = [
            'strength', 'perception', 'endurance', 'charisma',
            'intelligence', 'agility', 'luck'
        ]
        if 0 <= field_index < len(stat_names):
            return stat_names[field_index]
        return 'strength'  # Default

    def _compare_values(self, actual_value: Any, compare_type: CompareType, expected_value: str) -> bool:
        """Compare actual value with expected value"""
        try:
            expected = float(expected_value) if '.' in expected_value else int(expected_value)
            actual = float(actual_value) if isinstance(actual_value, (int, float)) else 0

            if compare_type == CompareType.EQUAL:
                return actual == expected
            elif compare_type == CompareType.NOT_EQUAL:
                return actual != expected
            elif compare_type == CompareType.LARGER_THAN:
                return actual > expected
            elif compare_type == CompareType.LESS_THAN:
                return actual < expected
            elif compare_type == CompareType.LARGER_EQUAL:
                return actual >= expected
            elif compare_type == CompareType.LESS_EQUAL:
                return actual <= expected

        except (ValueError, TypeError):
            # If conversion fails, do string comparison
            actual_str = str(actual_value)
            if compare_type == CompareType.EQUAL:
                return actual_str == expected_value
            elif compare_type == CompareType.NOT_EQUAL:
                return actual_str != expected_value

        return False