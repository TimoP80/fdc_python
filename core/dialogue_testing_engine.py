"""
Dialogue Testing Engine for testing dialogue flow
Provides comprehensive testing capabilities for Fallout dialogue files

This engine validates FMF (Fallout dialogue format) files by:
- Checking structural integrity (duplicate nodes, empty names, etc.)
- Validating all node links (including special terminal nodes: "done", "combat")
- Simulating dialogue flows from starting nodes with configurable depth limits
- Detecting potential infinite loops using graph traversal algorithms
- Testing condition evaluation (framework ready for full implementation)
- Generating detailed reports with categorized issues (Errors, Warnings, Info)

Special FMF Nodes:
- "done": Ends the dialogue normally
- "combat": Initiates combat sequence

Usage:
    from core.dialogue_testing_engine import DialogueTestingEngine

    engine = DialogueTestingEngine()
    report = engine.test_dialogue(dialogue)
    print(engine.generate_report_text(report))
"""

from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

from models.dialogue import (
    Dialogue, DialogueNode, PlayerOption, Condition,
    PlayerCharacter, CheckType, CompareType, Reaction, Gender
)
from .scripting_engine import ScriptingEngine, DialogueScriptContext, ScriptExecutionReport

logger = logging.getLogger(__name__)

class TestResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class TestIssue:
    """Represents a single test issue or finding"""
    severity: TestResult
    category: str
    message: str
    node_name: str = ""
    option_index: int = -1
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FlowPath:
    """Represents a path through the dialogue"""
    nodes: List[str] = field(default_factory=list)
    choices: List[str] = field(default_factory=list)
    conditions_met: List[bool] = field(default_factory=list)
    depth: int = 0
    terminated: bool = False
    termination_reason: str = ""

@dataclass
class TestReport:
    """Comprehensive test report"""
    dialogue_name: str = ""
    total_nodes: int = 0
    total_options: int = 0
    issues: List[TestIssue] = field(default_factory=list)
    flow_paths: List[FlowPath] = field(default_factory=list)
    orphaned_nodes: List[str] = field(default_factory=list)
    unreachable_nodes: List[str] = field(default_factory=list)
    loops_detected: List[List[str]] = field(default_factory=list)
    execution_time: float = 0.0

    def get_issue_count(self, severity: TestResult) -> int:
        return len([i for i in self.issues if i.severity == severity])

    def has_critical_issues(self) -> bool:
        return self.get_issue_count(TestResult.ERROR) > 0 or self.get_issue_count(TestResult.FAIL) > 0

class DialogueTestingEngine:
    """
    Engine for testing dialogue flow, validation, and structural integrity
    """

    def __init__(self, max_depth: int = 50, max_paths: int = 100):
        self.max_depth = max_depth
        self.max_paths = max_paths
        self.player_character = PlayerCharacter()  # Default test character
        self.scripting_engine = ScriptingEngine()

    def test_dialogue(self, dialogue: Dialogue) -> TestReport:
        """
        Run comprehensive tests on a dialogue
        """
        import time
        start_time = time.time()

        report = TestReport(dialogue_name=dialogue.npcname or "Unnamed Dialogue")
        report.total_nodes = len(dialogue.nodes)
        report.total_options = sum(len(node.options) for node in dialogue.nodes)

        logger.info(f"Starting dialogue testing for '{report.dialogue_name}' with {report.total_nodes} nodes")

        # Basic structural validation
        self._validate_structure(dialogue, report)

        # Link validation
        self._validate_links(dialogue, report)

        # Flow simulation
        self._simulate_flows(dialogue, report)

        # Loop detection
        self._detect_loops(dialogue, report)

        # Condition testing
        self._test_conditions(dialogue, report)

        # Script testing
        self._test_scripts(dialogue, report)

        report.execution_time = time.time() - start_time
        logger.info(f"Dialogue testing completed in {report.execution_time:.2f}s")
        return report

    def _validate_structure(self, dialogue: Dialogue, report: TestReport):
        """Validate basic dialogue structure"""
        logger.debug("Validating dialogue structure")

        # Check for duplicate node names
        node_names = {}
        for node in dialogue.nodes:
            if not node.nodename.strip():
                report.issues.append(TestIssue(
                    TestResult.ERROR,
                    "Structure",
                    "Node has empty or whitespace-only name",
                    details={"node_index": dialogue.nodes.index(node)}
                ))
                continue

            if node.nodename in node_names:
                report.issues.append(TestIssue(
                    TestResult.ERROR,
                    "Structure",
                    f"Duplicate node name: '{node.nodename}'",
                    node.nodename,
                    details={"first_occurrence": node_names[node.nodename]}
                ))
            else:
                node_names[node.nodename] = dialogue.nodes.index(node)

        # Check for nodes with no content
        for node in dialogue.nodes:
            if not node.npctext and not node.options and not node.customcode:
                report.issues.append(TestIssue(
                    TestResult.WARNING,
                    "Structure",
                    "Node has no NPC text, options, or custom code",
                    node.nodename
                ))

        # Check for starting node
        has_starting_node = any(node.is_wtg for node in dialogue.nodes)
        if not has_starting_node:
            report.issues.append(TestIssue(
                TestResult.WARNING,
                "Structure",
                "No starting node (is_wtg = true) found"
            ))

    def _validate_links(self, dialogue: Dialogue, report: TestReport):
        """Validate all node links"""
        logger.debug("Validating node links")

        node_names = {node.nodename for node in dialogue.nodes}

        # Special node names that are valid in FMF format
        special_nodes = {"done", "combat"}

        for node in dialogue.nodes:
            for i, option in enumerate(node.options):
                if not option.nodelink.strip():
                    report.issues.append(TestIssue(
                        TestResult.ERROR,
                        "Links",
                        "Option has empty link target",
                        node.nodename,
                        i,
                        {"option_text": option.optiontext[:50]}
                    ))
                    continue

                # Check if link is valid (either exists as a node or is a special node)
                if option.nodelink not in node_names and option.nodelink not in special_nodes:
                    report.issues.append(TestIssue(
                        TestResult.ERROR,
                        "Links",
                        f"Option links to non-existent node: '{option.nodelink}'",
                        node.nodename,
                        i,
                        {"option_text": option.optiontext[:50], "target": option.nodelink}
                    ))

        # Find orphaned nodes (nodes not referenced by any option)
        referenced_nodes = set()
        for node in dialogue.nodes:
            for option in node.options:
                if option.nodelink:
                    referenced_nodes.add(option.nodelink)

        # Add starting nodes to referenced set
        for node in dialogue.nodes:
            if node.is_wtg:
                referenced_nodes.add(node.nodename)

        orphaned = [node.nodename for node in dialogue.nodes if node.nodename not in referenced_nodes]
        report.orphaned_nodes = orphaned

        if orphaned:
            for orphan in orphaned:
                report.issues.append(TestIssue(
                    TestResult.WARNING,
                    "Links",
                    f"Orphaned node (not referenced by any option): '{orphan}'",
                    orphan
                ))

    def _simulate_flows(self, dialogue: Dialogue, report: TestReport):
        """Simulate dialogue flows from starting nodes"""
        logger.debug("Simulating dialogue flows")

        # Find starting nodes
        starting_nodes = [node for node in dialogue.nodes if node.is_wtg]

        if not starting_nodes:
            report.issues.append(TestIssue(
                TestResult.ERROR,
                "Flow",
                "No starting nodes found for flow simulation"
            ))
            return

        visited_nodes = set()
        all_paths = []

        for start_node in starting_nodes:
            logger.debug(f"Simulating flow from starting node: {start_node.nodename}")
            paths = self._explore_from_node(dialogue, start_node.nodename, [], [], 0, visited_nodes.copy())
            all_paths.extend(paths)

            # Limit total paths to prevent excessive computation
            if len(all_paths) >= self.max_paths:
                logger.warning(f"Reached maximum path limit ({self.max_paths}), stopping exploration")
                break

        report.flow_paths = all_paths[:self.max_paths]  # Limit stored paths

        # Check for unreachable nodes
        reachable_nodes = set()
        for path in all_paths:
            reachable_nodes.update(path.nodes)

        unreachable = [node.nodename for node in dialogue.nodes if node.nodename not in reachable_nodes]
        report.unreachable_nodes = unreachable

        if unreachable:
            for unreachable_node in unreachable:
                report.issues.append(TestIssue(
                    TestResult.WARNING,
                    "Flow",
                    f"Unreachable node: '{unreachable_node}'",
                    unreachable_node
                ))

    def _explore_from_node(self, dialogue: Dialogue, current_node_name: str,
                          path: List[str], choices: List[str], depth: int,
                          visited: Set[str]) -> List[FlowPath]:
        """Recursively explore dialogue from a node"""
        if depth >= self.max_depth:
            flow_path = FlowPath(
                nodes=path + [current_node_name],
                choices=choices,
                depth=depth,
                terminated=True,
                termination_reason=f"Maximum depth ({self.max_depth}) reached"
            )
            return [flow_path]

        if current_node_name in visited:
            # Loop detected - this will be handled separately
            flow_path = FlowPath(
                nodes=path + [current_node_name],
                choices=choices,
                depth=depth,
                terminated=True,
                termination_reason="Loop detected"
            )
            return [flow_path]

        visited.add(current_node_name)
        path = path + [current_node_name]

        current_node = None
        for node in dialogue.nodes:
            if node.nodename == current_node_name:
                current_node = node
                break

        if not current_node:
            flow_path = FlowPath(
                nodes=path,
                choices=choices,
                depth=depth,
                terminated=True,
                termination_reason=f"Node not found: {current_node_name}"
            )
            return [flow_path]

        # If node has no options, it's a terminal node
        if not current_node.options:
            flow_path = FlowPath(
                nodes=path,
                choices=choices,
                depth=depth,
                terminated=True,
                termination_reason="Terminal node (no options)"
            )
            return [flow_path]

        # Check for special terminal nodes
        if current_node.nodename.lower() in ["done", "combat"]:
            flow_path = FlowPath(
                nodes=path,
                choices=choices,
                depth=depth,
                terminated=True,
                termination_reason=f"Terminal node ({current_node.nodename})"
            )
            return [flow_path]

        # Explore each option
        all_paths = []
        for i, option in enumerate(current_node.options):
            if len(all_paths) >= self.max_paths:
                break

            # Check if conditions are met (simplified - always assume true for now)
            condition_met = self._evaluate_conditions(option.conditions, self.player_character)

            new_choices = choices + [f"{i}: {option.optiontext[:30]}..."]

            if condition_met:
                # Follow the link
                if option.nodelink.lower() in ["done", "combat"]:
                    # Special terminal nodes - create terminated path
                    flow_path = FlowPath(
                        nodes=path + [option.nodelink],
                        choices=new_choices,
                        conditions_met=[condition_met],
                        depth=depth + 1,
                        terminated=True,
                        termination_reason=f"Terminal link to {option.nodelink}"
                    )
                    all_paths.append(flow_path)
                else:
                    sub_paths = self._explore_from_node(
                        dialogue, option.nodelink, path, new_choices,
                        depth + 1, visited.copy()
                    )
                    all_paths.extend(sub_paths)
            else:
                # Condition not met - create terminated path
                flow_path = FlowPath(
                    nodes=path,
                    choices=new_choices,
                    conditions_met=[condition_met],
                    depth=depth + 1,
                    terminated=True,
                    termination_reason="Condition not met"
                )
                all_paths.append(flow_path)

        return all_paths

    def _detect_loops(self, dialogue: Dialogue, report: TestReport):
        """Detect potential infinite loops in dialogue"""
        logger.debug("Detecting loops in dialogue")

        loops = []
        visited = set()
        recursion_stack = set()

        def dfs(node_name: str, path: List[str]):
            if node_name in recursion_stack:
                # Found a loop
                loop_start = path.index(node_name)
                loop = path[loop_start:] + [node_name]
                loops.append(loop)
                return

            if node_name in visited:
                return

            visited.add(node_name)
            recursion_stack.add(node_name)
            path.append(node_name)

            # Find node and explore its options
            for node in dialogue.nodes:
                if node.nodename == node_name:
                    for option in node.options:
                        if option.nodelink:
                            dfs(option.nodelink, path.copy())
                    break

            path.pop()
            recursion_stack.remove(node_name)

        # Check all nodes
        for node in dialogue.nodes:
            if node.nodename not in visited:
                dfs(node.nodename, [])

        report.loops_detected = loops

        if loops:
            for loop in loops:
                report.issues.append(TestIssue(
                    TestResult.WARNING,
                    "Loops",
                    f"Potential infinite loop detected: {' -> '.join(loop)}",
                    loop[0],
                    details={"loop_path": loop}
                ))

    def _test_conditions(self, dialogue: Dialogue, report: TestReport):
        """Test condition evaluation"""
        logger.debug("Testing condition evaluation")

        for node in dialogue.nodes:
            for i, option in enumerate(node.options):
                if option.conditions:
                    try:
                        result = self._evaluate_conditions(option.conditions, self.player_character)
                        # Log condition evaluation for debugging
                        logger.debug(f"Condition evaluation for {node.nodename} option {i}: {result}")
                    except Exception as e:
                        report.issues.append(TestIssue(
                            TestResult.ERROR,
                            "Conditions",
                            f"Error evaluating conditions: {str(e)}",
                            node.nodename,
                            i,
                            {"error": str(e), "conditions": [str(c) for c in option.conditions]}
                        ))

    def _test_scripts(self, dialogue: Dialogue, report: TestReport):
        """Test script execution and validation"""
        logger.debug("Testing script execution")

        # Test custom procedures
        for proc in dialogue.customprocs:
            if proc.lines.strip():
                try:
                    # Create script context
                    context = DialogueScriptContext(
                        dialogue=dialogue,
                        player=self.player_character,
                        variables={var.name: var.value for var in dialogue.variables}
                    )

                    # Execute script
                    script_report = self.scripting_engine.execute_script(proc.lines, context)

                    if script_report.result != ScriptExecutionReport.ScriptResult.SUCCESS:
                        severity = TestResult.ERROR if script_report.result in [
                            ScriptExecutionReport.ScriptResult.SECURITY_VIOLATION,
                            ScriptExecutionReport.ScriptResult.ERROR
                        ] else TestResult.WARNING

                        report.issues.append(TestIssue(
                            severity,
                            "Scripts",
                            f"Script execution failed in procedure '{proc.name}': {script_report.error_message}",
                            details={
                                "procedure": proc.name,
                                "result": script_report.result.value,
                                "execution_time": script_report.execution_time,
                                "security_violations": script_report.security_violations
                            }
                        ))

                except Exception as e:
                    report.issues.append(TestIssue(
                        TestResult.ERROR,
                        "Scripts",
                        f"Exception during script testing in procedure '{proc.name}': {str(e)}",
                        details={"procedure": proc.name, "error": str(e)}
                    ))

        # Test node custom code
        for node in dialogue.nodes:
            if node.customcode.strip():
                try:
                    context = DialogueScriptContext(
                        dialogue=dialogue,
                        player=self.player_character,
                        current_node=node,
                        variables={var.name: var.value for var in dialogue.variables}
                    )

                    script_report = self.scripting_engine.execute_script(node.customcode, context)

                    if script_report.result != ScriptExecutionReport.ScriptResult.SUCCESS:
                        severity = TestResult.ERROR if script_report.result in [
                            ScriptExecutionReport.ScriptResult.SECURITY_VIOLATION,
                            ScriptExecutionReport.ScriptResult.ERROR
                        ] else TestResult.WARNING

                        report.issues.append(TestIssue(
                            severity,
                            "Scripts",
                            f"Script execution failed in node '{node.nodename}': {script_report.error_message}",
                            node.nodename,
                            details={
                                "result": script_report.result.value,
                                "execution_time": script_report.execution_time,
                                "security_violations": script_report.security_violations
                            }
                        ))

                except Exception as e:
                    report.issues.append(TestIssue(
                        TestResult.ERROR,
                        "Scripts",
                        f"Exception during script testing in node '{node.nodename}': {str(e)}",
                        node.nodename,
                        details={"error": str(e)}
                    ))

    def _evaluate_conditions(self, conditions: List[Condition], player: PlayerCharacter) -> bool:
        """
        Evaluate a list of conditions against player character
        Simplified implementation - returns True for now
        """
        if not conditions:
            return True

        # TODO: Implement full condition evaluation logic
        # This would check stats, skills, inventory, etc.
        return True

    def generate_report_text(self, report: TestReport) -> str:
        """Generate human-readable test report"""
        lines = []
        lines.append(f"Dialogue Testing Report: {report.dialogue_name}")
        lines.append("=" * 50)
        lines.append(f"Total Nodes: {report.total_nodes}")
        lines.append(f"Total Options: {report.total_options}")
        lines.append(f"Execution Time: {report.execution_time:.2f}s")
        lines.append("")

        # Issue summary
        lines.append("ISSUE SUMMARY:")
        lines.append(f"Errors: {report.get_issue_count(TestResult.ERROR)}")
        lines.append(f"Failures: {report.get_issue_count(TestResult.FAIL)}")
        lines.append(f"Warnings: {report.get_issue_count(TestResult.WARNING)}")
        lines.append("")

        # Flow analysis
        lines.append("FLOW ANALYSIS:")
        lines.append(f"Flow Paths Explored: {len(report.flow_paths)}")
        lines.append(f"Orphaned Nodes: {len(report.orphaned_nodes)}")
        lines.append(f"Unreachable Nodes: {len(report.unreachable_nodes)}")
        lines.append(f"Loops Detected: {len(report.loops_detected)}")
        lines.append("")

        # Script analysis
        script_issues = [i for i in report.issues if i.category == "Scripts"]
        if script_issues:
            lines.append("SCRIPT ANALYSIS:")
            lines.append(f"Script Issues: {len(script_issues)}")
            lines.append("")

        # Detailed issues
        if report.issues:
            lines.append("DETAILED ISSUES:")
            for issue in report.issues:
                severity_icon = {
                    TestResult.ERROR: "❌",
                    TestResult.FAIL: "❌",
                    TestResult.WARNING: "⚠️"
                }.get(issue.severity, "?")
                lines.append(f"{severity_icon} [{issue.category}] {issue.message}")
                if issue.node_name:
                    lines.append(f"   Node: {issue.node_name}")
                if issue.option_index >= 0:
                    lines.append(f"   Option: {issue.option_index}")
                if issue.details:
                    for key, value in issue.details.items():
                        lines.append(f"   {key}: {value}")
                lines.append("")

        # Replace Unicode characters that might cause encoding issues
        result = "\n".join(lines)
        result = result.replace("❌", "[ERROR]")
        result = result.replace("⚠️", "[WARNING]")
        result = result.replace("✅", "[PASS]")
        return result