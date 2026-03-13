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


class Skill(Enum):
    """Fallout 1/2 Skills"""
    SMALL_GUNS = 0
    BIG_GUNS = 1
    ENERGY_WEAPONS = 2
    UNARMED = 3
    MELEE_WEAPONS = 4
    THROWING = 5
    FIRST_AID = 6
    DOCTOR = 7
    SNEAK = 8
    LOCKPICK = 11
    STEAL = 12
    TRAPS = 13
    SCIENCE = 14
    REPAIR = 15
    SPEECH = 16
    BARTER = 17
    GAMBLING = 18
    OUTDOORSMAN = 19

    @classmethod
    def get_name(cls, value: int) -> str:
        """Get skill name by value"""
        for skill in cls:
            if skill.value == value:
                return skill.name.replace('_', ' ').title()
        return f"Unknown ({value})"

    @classmethod
    def from_name(cls, name: str) -> 'Skill':
        """Get skill by name"""
        name_upper = name.upper().replace(' ', '_')
        try:
            return cls[name_upper]
        except KeyError:
            return cls.SMALL_GUNS


class FloatMessageType(Enum):
    """Types of float messages"""
    NPC_DIALOGUE = 0
    PLAYER_RESPONSE = 1
    SYSTEM_NOTIFICATION = 2
    CONDITION_CHECK = 3
    SKILL_CHECK = 4


@dataclass
class FloatMessage:
    """Represents a single floating message"""
    text: str = ""
    message_type: FloatMessageType = FloatMessageType.NPC_DIALOGUE
    position_x: float = 0.0
    position_y: float = 0.0
    color: str = "#FFFFFF"  # Default white
    font_size: int = 12
    is_visible: bool = True
    fade_in: float = 0.0  # seconds
    fade_out: float = 0.0  # seconds
    duration: float = 3.0  # seconds to display


@dataclass
class FloatMessagePosition(Enum):
    """Position of float message relative to node"""
    ABOVE = 0
    BELOW = 1
    LEFT = 2
    RIGHT = 3
    CENTER = 4

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
    optiontext: str = ""
    nodelink: str = ""
    noderesolved: int = -1
    link_to_proc: bool = False
    link_to_skillcheck: bool = False
    reaction: Reaction = Reaction.NEUTRAL
    genderflags: Gender = Gender.NONE
    intcheck: int = 4
    notes: str = ""
    conditions: List[Condition] = field(default_factory=list)
    conditioncnt: int = 0
    # Skill check for this option
    has_skill_check: bool = False
    skill_check: Optional['SkillCheck'] = None
    # Alternate responses based on skill check result
    success_response: str = ""
    failure_response: str = ""
    # Position in diagram
    position_x: float = 0.0
    position_y: float = 0.0

@dataclass
class SkillCheck:
    """Represents a skill check definition"""
    check_proc_name: str = ""
    check_what: Skill = Skill.SPEECH  # Skill being checked
    modifier: int = 0  # Additional modifier to skill check
    successnode: str = ""  # Node to go to on success
    failurenode: str = ""  # Node to go to on failure
    required_value: int = 0  # Minimum skill value to pass
    is_percentage: bool = False  # If true, check is percentage-based
    script_on_success: str = ""  # Custom script to run on success
    script_on_failure: str = ""  # Custom script to run on failure
    notes: str = ""  # Designer notes

    def get_skill_name(self) -> str:
        """Get the name of the skill being checked"""
        return Skill.get_name(self.check_what.value if isinstance(self.check_what, Skill) else self.check_what)

    def to_condition_code(self) -> str:
        """Generate condition code for skill check"""
        skill_name = self.get_skill_name().upper().replace(' ', '_')
        if self.is_percentage:
            return f"trait_{skill_name}() >= {self.required_value}"
        else:
            return f"skill_{skill_name}() >= {self.required_value}"

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
    # Enhanced float messages with full properties
    float_messages: List[FloatMessage] = field(default_factory=list)
    position_x: float = 0.0  # X position in diagram
    position_y: float = 0.0  # Y position in diagram
    is_visible: bool = True
    background_color: str = "#000000"  # Background color
    border_color: str = "#00FF00"  # Border color (terminal green)
    text_color: str = "#00FF00"  # Text color

    def add_message(self, text: str, msg_type: FloatMessageType = FloatMessageType.NPC_DIALOGUE) -> FloatMessage:
        """Add a new float message to this node"""
        msg = FloatMessage(text=text, message_type=msg_type)
        self.float_messages.append(msg)
        self.messages.append(text)
        self.messagecnt = len(self.messages)
        return msg

    def remove_message(self, index: int):
        """Remove a message by index"""
        if 0 <= index < len(self.float_messages):
            del self.float_messages[index]
        if 0 <= index < len(self.messages):
            del self.messages[index]
        self.messagecnt = len(self.messages)

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