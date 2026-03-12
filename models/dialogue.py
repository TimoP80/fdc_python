"""
Data models for Fallout Dialogue Creator
Based on the original Delphi SharedDLGData.pas structures
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

class Reaction(Enum):
    NEUTRAL = 0
    GOOD = 1
    BAD = 2

class Gender(Enum):
    NONE = 0
    MALE = 1
    FEMALE = 2

class CheckType(Enum):
    STAT = 1
    SKILL = 2
    MONEY = 3
    GLOBAL_VAR = 4
    LOCAL_VAR = 5
    SCRIPT_VAR = 6
    ITEM_PLAYER = 7
    CUSTOM_CODE = 8

class CompareType(Enum):
    EQUAL = 1
    NOT_EQUAL = 2
    LARGER_THAN = 3
    LESS_THAN = 4
    LARGER_EQUAL = 5
    LESS_EQUAL = 6

class LinkType(Enum):
    NONE = 0
    AND = 1
    OR = 2

@dataclass
class Condition:
    """Represents a condition for player options"""
    check_type: CheckType
    check_field: int
    check_eval: CompareType
    var_ptr: str = ""
    check_value: str = ""
    resolved_code: str = ""
    link: LinkType = LinkType.NONE

@dataclass
class PlayerOption:
    """Represents a player dialogue option"""
    optiontext: str
    nodelink: str
    noderesolved: int = -1
    link_to_proc: bool = False
    link_to_skillcheck: bool = False
    reaction: Reaction = Reaction.NEUTRAL
    genderflags: Gender = Gender.NONE
    intcheck: int = 4
    notes: str = ""
    conditions: List[Condition] = field(default_factory=list)
    conditioncnt: int = 0

@dataclass
class SkillCheck:
    """Represents a skill check definition"""
    check_proc_name: str
    check_what: int
    modifier: int
    successnode: str
    failurenode: str

@dataclass
class DialogueNode:
    """Represents a dialogue node"""
    is_wtg: bool = False  # "What to say" - starting node
    customcode: str = ""
    skillchecks: List[SkillCheck] = field(default_factory=list)
    skillcheckcnt: int = 0
    nodename: str = ""
    npctext: str = ""
    npctext_female: str = ""
    notes: str = ""
    hidden: bool = False
    options: List[PlayerOption] = field(default_factory=list)
    optioncnt: int = 0

@dataclass
class FloatNode:
    """Represents a floating message node"""
    nodename: str = ""
    notes: str = ""
    messages: List[str] = field(default_factory=list)
    messagecnt: int = 0

@dataclass
class Action:
    """Represents a timed event action"""
    linedata: str = ""

@dataclass
class TimeEvent:
    """Represents a timed event"""
    fixedparamname: str = ""
    fixedparamenumindex: int = 0
    actionlines: List[Action] = field(default_factory=list)
    actioncnt: int = 0
    israndom: bool = False
    mininterval: int = 0
    maxinterval: int = 0
    interval: int = 0

@dataclass
class Variable:
    """Represents a dialogue variable"""
    name: str = ""
    flags: int = 0  # VAR_FLAGS_*
    vartype: int = 0  # VAR_TYPE_*
    notes: str = ""
    value: Any = None

@dataclass
class StartingCondition:
    """Represents dialogue starting conditions"""
    conditions: List[Condition] = field(default_factory=list)
    condcnt: int = 0
    goto_node: str = ""

@dataclass
class CustomProcedure:
    """Represents a custom procedure"""
    name: str = ""
    lines: str = ""
    associatewithnode: int = 0

@dataclass
class Dialogue:
    """Main dialogue container"""
    filename: str = ""
    npcname: str = ""
    description: str = ""
    location: str = ""
    unknowndesc: str = ""
    knowndesc: str = ""
    detaileddesc: str = ""

    # Timing
    start_time_event: int = 0

    # Conditions
    startconditions: List[StartingCondition] = field(default_factory=list)
    startconditioncnt: int = 0
    default_cond: int = -1

    # Procedures
    customprocs: List[CustomProcedure] = field(default_factory=list)
    customproccnt: int = 0

    # Events
    timedevents: List[TimeEvent] = field(default_factory=list)
    timedeventcnt: int = 0

    # Float messages
    floatnodes: List[FloatNode] = field(default_factory=list)
    floatnodecount: int = 0

    # Main content
    nodes: List[DialogueNode] = field(default_factory=list)
    nodecount: int = 0

    # Variables
    variables: List[Variable] = field(default_factory=list)
    varcnt: int = 0

    def get_node_index(self, name: str) -> int:
        """Find node by name (case insensitive)"""
        name_lower = name.lower()
        for i, node in enumerate(self.nodes):
            if node.nodename.lower() == name_lower:
                return i
        return -1

    def get_float_node_index(self, name: str) -> int:
        """Find float node by name"""
        name_lower = name.lower()
        for i, node in enumerate(self.floatnodes):
            if node.nodename.lower() == name_lower:
                return i
        return -1

    def resolve_nodes(self):
        """Resolve node links to indices"""
        for node in self.nodes:
            for option in node.options:
                option.noderesolved = self.get_node_index(option.nodelink)

@dataclass
class PlayerCharacter:
    """Player character data"""
    name: str = ""
    gender: Gender = Gender.MALE
    age: int = 16
    strength: int = 5
    perception: int = 5
    endurance: int = 5
    charisma: int = 5
    intelligence: int = 5
    agility: int = 5
    luck: int = 5
    dude_caps: int = 0
    skills: List[Dict[str, Any]] = field(default_factory=lambda: [{} for _ in range(18)])

# Constants (migrated from Delphi)
VAR_FLAGS_NONE = 0
VAR_FLAGS_IMPORT = 1
VAR_FLAGS_EXPORT = 2
VAR_FLAGS_LOCAL = 3
VAR_FLAGS_GLOBAL = 4

VAR_TYPE_STRING = 0
VAR_TYPE_INT = 1
VAR_TYPE_FLOAT = 2

FIELD_NPC_NAME = 0
FIELD_NPC_LOCATION = 1
FIELD_NPC_DESCRIPTION = 2
FIELD_NPC_UNKNOWN_LOOK = 3
FIELD_NPC_KNOWN_LOOK = 4
FIELD_NPC_DETAILED_LOOK = 5
FIELD_NODE_NPCTEXT = 6
FIELD_NODE_NPCFEMALETEXT = 7
FIELD_NODE_NOTES = 8
FIELD_NODE_NAME = 16
FIELD_PLAYEROPTION_OPTIONTEXT = 10
FIELD_PLAYEROPTION_REACTION = 11
FIELD_PLAYEROPTION_GENDERFLAGS = 12
FIELD_PLAYEROPTION_NODELINK = 13
FIELD_PLAYEROPTION_INTCHECK = 14
FIELD_PLAYEROPTION_NOTES = 15