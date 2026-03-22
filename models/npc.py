"""
Data models for NPC (Non-Player Character) configuration
Extends the dialogue system with comprehensive NPC properties
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from models.dialogue import Gender, Skill, Dialogue, DialogueNode, PlayerOption


class NpcClass(Enum):
    """NPC profession/role classes"""
    CIVILIAN = 0
    MERCHANT = 1
    GUARD = 2
    SOLDIER = 3
    SCIENTIST = 4
    DOCTOR = 5
    CHILD = 6
    ELDER = 7
    LEADER = 8
    SCRAP = 9
    ANIMAL = 10
    ROBOT = 13
    ALIEN = 14
    SUPER_MUTANT = 15
    GHOUL = 16
    ROBOT_HUMAN = 17
    CUSTOM = 99

    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name.replace('_', ' ').title()
        return f"Unknown ({value})"


class AiPackage(Enum):
    """AI package types for NPC behavior"""
    NONE = 0
    GUARD = 1
    ESCORT = 2
    RUN_AWAY = 3
    SPECIAL_GUARD = 4
    TALKER = 5
    LEADER = 6
    FOLLOWER = 7
    ANIMATED = 8
    SCAVENGER = 9
    PATROL = 10
    EQUIPMENT = 11
    FOLLOWER_SLEEP = 12
    SENTRY = 13
    PANIC = 14
    LOOTER = 15
    FISSION = 16

    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name.replace('_', ' ').title()
        return f"Unknown ({value})"


class NpcStat(Enum):
    """NPC statistics/enumerations"""
    HIT_POINTS = 0
    ACTION_POINTS = 1
    ARMOR_CLASS = 2
    MELEE_DAMAGE = 3
    SEQUENCE = 4
    HEALING_RATE = 5
    CRITICAL_CHANCE = 6
    BETTER_CRITICALS = 7
    RADIATION_RESISTANCE = 8
    POISON_RESISTANCE = 9
    DAMAGE_THRESHOLD_NORMAL = 10
    DAMAGE_THRESHOLD_LASER = 11
    DAMAGE_THRESHOLD_FIRE = 12
    DAMAGE_THRESHOLD_PLASMA = 13
    DAMAGE_THRESHOLD_ELECTRICAL = 14
    DAMAGE_THRESHOLD_EXPLOSIVE = 15
    DAMAGE_THRESHOLD_HP = 16

    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name.replace('_', ' ').title()
        return f"Unknown ({value})"


class RelationshipType(Enum):
    """Types of relationships with the player"""
    NEUTRAL = 0
    FRIEND = 1
    ENEMY = 2
    LOVER = 3
    PET = 4
    SERVANT = 5
    MASTER = 6
    COMRADE = 7

    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name.replace('_', ' ').title()
        return f"Unknown ({value})"


class ReputationType(Enum):
    """Reputation types"""
    NONE = 0
    GOOD = 1
    BAD = 2
    GANGS = 3
    VILLAGERS = 4
    OTHER = 5

    @classmethod
    def get_name(cls, value: int) -> str:
        for item in cls:
            if item.value == value:
                return item.name.replace('_', ' ').title()
        return f"Unknown ({value})"


@dataclass
class Appearance:
    """NPC appearance configuration"""
    # Basic appearance
    fid: int = 0  # Frm ID (file ID)
    head_fid: int = 0  # Head frm ID
    body_fid: int = 0  # Body frm ID
    animation_code: str = ""
    
    # Colors
    skin_color: str = "#d4a574"
    hair_color: str = "#2d2d2d"
    primary_color: str = "#5c4033"
    secondary_color: str = "#3d2b1f"
    
    # Features
    hairstyle: str = "Default"
    facial_hair: str = "None"
    makeup: str = "None"
    scars: List[str] = field(default_factory=list)
    
    # Equipment appearance
    armor_fid: int = 0
    weapon_fid: int = 0


@dataclass
class NpcAttribute:
    """NPC attribute (SPECIAL) values"""
    strength: int = 5
    perception: int = 5
    endurance: int = 5
    charisma: int = 5
    intelligence: int = 5
    agility: int = 5
    luck: int = 5
    
    # Derived stats
    hit_points: int = 20
    max_hit_points: int = 20
    action_points: int = 5
    armor_class: int = 0
    melee_damage: int = 0
    sequence: int = 5
    healing_rate: int = 0
    critical_chance: int = 0
    
    # Resistances
    radiation_resistance: int = 0
    poison_resistance: int = 0
    
    # Damage thresholds
    dt_normal: int = 0
    dt_laser: int = 0
    dt_fire: int = 0
    dt_plasma: int = 0
    dt_electrical: int = 0
    dt_explosive: int = 0
    
    def get_total_special(self) -> int:
        """Get total of all SPECIAL stats"""
        return (self.strength + self.perception + self.endurance + 
                self.charisma + self.intelligence + self.agility + self.luck)
    
    def validate(self) -> List[str]:
        """Validate attribute values and return list of errors"""
        errors = []
        stats = [
            ("Strength", self.strength, 1, 10),
            ("Perception", self.perception, 1, 10),
            ("Endurance", self.endurance, 1, 10),
            ("Charisma", self.charisma, 1, 10),
            ("Intelligence", self.intelligence, 1, 10),
            ("Agility", self.agility, 1, 10),
            ("Luck", self.luck, 1, 10),
        ]
        
        for name, value, min_val, max_val in stats:
            if value < min_val or value > max_val:
                errors.append(f"{name} must be between {min_val} and {max_val}")
        
        if self.hit_points < 0:
            errors.append("Hit points cannot be negative")
        if self.max_hit_points < 1:
            errors.append("Max hit points must be at least 1")
        if self.action_points < 0:
            errors.append("Action points cannot be negative")
            
        return errors


@dataclass
class SkillValue:
    """NPC skill value with bonus"""
    skill: Skill
    value: int = 0
    bonus: int = 0
    
    @property
    def total(self) -> int:
        return self.value + self.bonus


@dataclass
class InventoryItem:
    """NPC inventory item"""
    pid: int = 0  # Proto ID
    item_name: str = ""
    quantity: int = 1
    condition: int = 100  # 0-100 percentage
    charges: int = 0
    is_equipped: bool = False
    is_locked: bool = False
    ammo_pid: int = 0  # Ammo type
    ammo_quantity: int = 0
    
    def validate(self) -> List[str]:
        """Validate item and return list of errors"""
        errors = []
        if self.quantity < 1:
            errors.append("Quantity must be at least 1")
        if self.condition < 0 or self.condition > 100:
            errors.append("Condition must be between 0 and 100")
        return errors


@dataclass
class BehaviorPattern:
    """NPC behavior pattern configuration"""
    # General behavior
    aggression: int = 0  # 0-100
    cowardice: int = 0  # 0-100
    enthusiasm: int = 50  # 0-100
    
    # AI settings
    ai_number: int = 0
    ai_package: AiPackage = AiPackage.NONE
    
    # Script references
    script_id: int = 0
    script_name: str = ""
    
    # Movement
    movement_type: str = "Walk"
    run_distance: int = 10
    
    # Combat
    combat_style: str = "Default"
    primary_weapon: str = ""
    secondary_weapon: str = ""
    
    # Schedule
    has_schedule: bool = False
    schedule_data: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate behavior patterns"""
        errors = []
        if self.aggression < 0 or self.aggression > 100:
            errors.append("Aggression must be between 0 and 100")
        if self.cowardice < 0 or self.cowardice > 100:
            errors.append("Cowardice must be between 0 and 100")
        if self.enthusiasm < 0 or self.enthusiasm > 100:
            errors.append("Enthusiasm must be between 0 and 100")
        return errors


@dataclass
class AiSettings:
    """Advanced AI behavior settings"""
    # General AI
    brain_type: str = "Default"
    packet_type: AiPackage = AiPackage.NONE
    
    # Perception
    perception_radius: int = 10
    vision_range: int = 10
    hearing_range: int = 10
    
    # Combat
    attack_rate: int = 3
    min_hit_chance: int = 0
    max_distance: int = 15
    min_distance: int = 0
    
    # Movement
    wander_radius: int = 5
    walk_speed: float = 1.0
    run_speed: float = 2.0
    
    # Reactions
    reaction_override: int = -1  # -1 = use default
    fear_trigger: int = 25
    
    # Special behaviors
    is_critical: bool = False
    can_loot: bool = True
    can_call_help: bool = True
    help_radius: int = 15
    
    # Group settings
    team_id: int = 0
    ai_group: int = 0


@dataclass
class Relationship:
    """NPC relationship with player/factions"""
    # Player relationship
    relation_type: RelationshipType = RelationshipType.NEUTRAL
    relation_modifier: int = 0  # -100 to 100
    
    # Faction relationships
    faction_id: int = 0
    faction_name: str = ""
    faction_standing: int = 0  # -100 to 100
    
    # Reputation
    reputation: int = 0
    reputation_type: ReputationType = ReputationType.NONE
    
    # Karma
    karma_level: str = "Neutral"
    
    def validate(self) -> List[str]:
        """Validate relationship settings"""
        errors = []
        if self.relation_modifier < -100 or self.relation_modifier > 100:
            errors.append("Relation modifier must be between -100 and 100")
        if self.faction_standing < -100 or self.faction_standing > 100:
            errors.append("Faction standing must be between -100 and 100")
        return errors


@dataclass
class NpcDialogue:
    """NPC dialogue association"""
    # Link to dialogue file
    dialogue_file: str = ""
    dialogue: Optional[Dialogue] = None
    
    # Starting conditions
    default_node: str = ""
    greeting_node: str = ""
    trade_node: str = ""
    
    # Special nodes
    death_node: str = ""
    knocked_out_node: str = ""
    
    # Reactions
    reaction_table: Dict[int, str] = field(default_factory=dict)


@dataclass
class Npc:
    """Complete NPC configuration"""
    # Basic identification
    id: int = 0
    name: str = ""
    description: str = ""
    comments: str = ""
    
    # File references
    fmf_file: str = ""
    
    # Classification
    npc_class: NpcClass = NpcClass.CIVILIAN
    gender: Gender = Gender.MALE
    age: int = 30
    
    # Sub-components
    appearance: Appearance = field(default_factory=Appearance)
    attributes: NpcAttribute = field(default_factory=NpcAttribute)
    skills: List[SkillValue] = field(default_factory=list)
    inventory: List[InventoryItem] = field(default_factory=list)
    behavior: BehaviorPattern = field(default_factory=BehaviorPattern)
    ai_settings: AiSettings = field(default_factory=AiSettings)
    relationship: Relationship = field(default_factory=Relationship)
    dialogue: NpcDialogue = field(default_factory=NpcDialogue)
    
    # Visual feedback
    is_modified: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize default skills if empty"""
        if not self.skills:
            self.skills = [SkillValue(skill=skill) for skill in Skill]
    
    def validate(self) -> bool:
        """Validate all NPC properties and return True if valid"""
        errors = []
        
        # Basic validation
        if not self.name or not self.name.strip():
            errors.append("NPC name is required")
        if len(self.name) > 32:
            errors.append("NPC name must be 32 characters or less")
        
        # Validate attributes
        attr_errors = self.attributes.validate()
        errors.extend(attr_errors)
        
        # Validate behavior
        behavior_errors = self.behavior.validate()
        errors.extend(behavior_errors)
        
        # Validate relationship
        rel_errors = self.relationship.validate()
        errors.extend(rel_errors)
        
        # Validate inventory
        for item in self.inventory:
            item_errors = item.validate()
            errors.extend([f"Item '{item.item_name}': {e}" for e in item_errors])
        
        self.validation_errors = errors
        return len(errors) == 0
    
    def get_validation_summary(self) -> str:
        """Get human-readable validation summary"""
        if self.validate():
            return "✓ All validations passed"
        
        lines = ["✗ Validation errors:"]
        for error in self.validation_errors:
            lines.append(f"  • {error}")
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert NPC to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "comments": self.comments,
            "fmf_file": self.fmf_file,
            "npc_class": self.npc_class.value,
            "gender": self.gender.value,
            "age": self.age,
            "appearance": {
                "fid": self.appearance.fid,
                "head_fid": self.appearance.head_fid,
                "body_fid": self.appearance.body_fid,
                "animation_code": self.appearance.animation_code,
                "skin_color": self.appearance.skin_color,
                "hair_color": self.appearance.hair_color,
                "primary_color": self.appearance.primary_color,
                "secondary_color": self.appearance.secondary_color,
                "hairstyle": self.appearance.hairstyle,
                "facial_hair": self.appearance.facial_hair,
                "makeup": self.appearance.makeup,
                "scars": self.appearance.scars,
                "armor_fid": self.appearance.armor_fid,
                "weapon_fid": self.appearance.weapon_fid,
            },
            "attributes": {
                "strength": self.attributes.strength,
                "perception": self.attributes.perception,
                "endurance": self.attributes.endurance,
                "charisma": self.attributes.charisma,
                "intelligence": self.attributes.intelligence,
                "agility": self.attributes.agility,
                "luck": self.attributes.luck,
                "hit_points": self.attributes.hit_points,
                "max_hit_points": self.attributes.max_hit_points,
                "action_points": self.attributes.action_points,
                "armor_class": self.attributes.armor_class,
                "melee_damage": self.attributes.melee_damage,
                "sequence": self.attributes.sequence,
                "healing_rate": self.attributes.healing_rate,
                "critical_chance": self.attributes.critical_chance,
                "radiation_resistance": self.attributes.radiation_resistance,
                "poison_resistance": self.attributes.poison_resistance,
                "dt_normal": self.attributes.dt_normal,
                "dt_laser": self.attributes.dt_laser,
                "dt_fire": self.attributes.dt_fire,
                "dt_plasma": self.attributes.dt_plasma,
                "dt_electrical": self.attributes.dt_electrical,
                "dt_explosive": self.attributes.dt_explosive,
            },
            "skills": {s.skill.name: s.total for s in self.skills},
            "inventory": [
                {
                    "pid": item.pid,
                    "name": item.item_name,
                    "quantity": item.quantity,
                    "condition": item.condition,
                    "charges": item.charges,
                    "is_equipped": item.is_equipped,
                }
                for item in self.inventory
            ],
            "behavior": {
                "aggression": self.behavior.aggression,
                "cowardice": self.behavior.cowardice,
                "enthusiasm": self.behavior.enthusiasm,
                "ai_number": self.behavior.ai_number,
                "ai_package": self.behavior.ai_package.value,
                "script_id": self.behavior.script_id,
                "script_name": self.behavior.script_name,
                "movement_type": self.behavior.movement_type,
                "run_distance": self.behavior.run_distance,
                "combat_style": self.behavior.combat_style,
                "primary_weapon": self.behavior.primary_weapon,
                "secondary_weapon": self.behavior.secondary_weapon,
            },
            "ai_settings": {
                "brain_type": self.ai_settings.brain_type,
                "packet_type": self.ai_settings.packet_type.value,
                "perception_radius": self.ai_settings.perception_radius,
                "vision_range": self.ai_settings.vision_range,
                "hearing_range": self.ai_settings.hearing_range,
                "attack_rate": self.ai_settings.attack_rate,
                "min_hit_chance": self.ai_settings.min_hit_chance,
                "max_distance": self.ai_settings.max_distance,
                "min_distance": self.ai_settings.min_distance,
                "wander_radius": self.ai_settings.wander_radius,
                "walk_speed": self.ai_settings.walk_speed,
                "run_speed": self.ai_settings.run_speed,
                "reaction_override": self.ai_settings.reaction_override,
                "fear_trigger": self.ai_settings.fear_trigger,
                "is_critical": self.ai_settings.is_critical,
                "can_loot": self.ai_settings.can_loot,
                "can_call_help": self.ai_settings.can_call_help,
                "help_radius": self.ai_settings.help_radius,
                "team_id": self.ai_settings.team_id,
                "ai_group": self.ai_settings.ai_group,
            },
            "relationship": {
                "relation_type": self.relationship.relation_type.value,
                "relation_modifier": self.relationship.relation_modifier,
                "faction_id": self.relationship.faction_id,
                "faction_name": self.relationship.faction_name,
                "faction_standing": self.relationship.faction_standing,
                "reputation": self.relationship.reputation,
                "reputation_type": self.relationship.reputation_type.value,
                "karma_level": self.relationship.karma_level,
            },
            "dialogue": {
                "dialogue_file": self.dialogue.dialogue_file,
                "default_node": self.dialogue.default_node,
                "greeting_node": self.dialogue.greeting_node,
                "trade_node": self.dialogue.trade_node,
                "death_node": self.dialogue.death_node,
                "knocked_out_node": self.dialogue.knocked_out_node,
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Npc':
        """Create NPC from dictionary"""
        npc = cls()
        
        # Basic fields
        npc.id = data.get("id", 0)
        npc.name = data.get("name", "")
        npc.description = data.get("description", "")
        npc.comments = data.get("comments", "")
        npc.fmf_file = data.get("fmf_file", "")
        npc.npc_class = NpcClass(data.get("npc_class", 0))
        npc.gender = Gender(data.get("gender", 1))
        npc.age = data.get("age", 30)
        
        # Appearance
        if "appearance" in data:
            app = data["appearance"]
            npc.appearance.fid = app.get("fid", 0)
            npc.appearance.head_fid = app.get("head_fid", 0)
            npc.appearance.body_fid = app.get("body_fid", 0)
            npc.appearance.animation_code = app.get("animation_code", "")
            npc.appearance.skin_color = app.get("skin_color", "#d4a574")
            npc.appearance.hair_color = app.get("hair_color", "#2d2d2d")
            npc.appearance.primary_color = app.get("primary_color", "#5c4033")
            npc.appearance.secondary_color = app.get("secondary_color", "#3d2b1f")
            npc.appearance.hairstyle = app.get("hairstyle", "Default")
            npc.appearance.facial_hair = app.get("facial_hair", "None")
            npc.appearance.makeup = app.get("makeup", "None")
            npc.appearance.scars = app.get("scars", [])
            npc.appearance.armor_fid = app.get("armor_fid", 0)
            npc.appearance.weapon_fid = app.get("weapon_fid", 0)
        
        # Attributes
        if "attributes" in data:
            attr = data["attributes"]
            npc.attributes.strength = attr.get("strength", 5)
            npc.attributes.perception = attr.get("perception", 5)
            npc.attributes.endurance = attr.get("endurance", 5)
            npc.attributes.charisma = attr.get("charisma", 5)
            npc.attributes.intelligence = attr.get("intelligence", 5)
            npc.attributes.agility = attr.get("agility", 5)
            npc.attributes.luck = attr.get("luck", 5)
            npc.attributes.hit_points = attr.get("hit_points", 20)
            npc.attributes.max_hit_points = attr.get("max_hit_points", 20)
            npc.attributes.action_points = attr.get("action_points", 5)
            npc.attributes.armor_class = attr.get("armor_class", 0)
            npc.attributes.melee_damage = attr.get("melee_damage", 0)
            npc.attributes.sequence = attr.get("sequence", 5)
            npc.attributes.healing_rate = attr.get("healing_rate", 0)
            npc.attributes.critical_chance = attr.get("critical_chance", 0)
            npc.attributes.radiation_resistance = attr.get("radiation_resistance", 0)
            npc.attributes.poison_resistance = attr.get("poison_resistance", 0)
            npc.attributes.dt_normal = attr.get("dt_normal", 0)
            npc.attributes.dt_laser = attr.get("dt_laser", 0)
            npc.attributes.dt_fire = attr.get("dt_fire", 0)
            npc.attributes.dt_plasma = attr.get("dt_plasma", 0)
            npc.attributes.dt_electrical = attr.get("dt_electrical", 0)
            npc.attributes.dt_explosive = attr.get("dt_explosive", 0)
        
        # Skills
        if "skills" in data:
            for skill_name, value in data["skills"].items():
                try:
                    skill = Skill[skill_name]
                    for sv in npc.skills:
                        if sv.skill == skill:
                            sv.value = value
                            break
                except KeyError:
                    pass
        
        # Inventory
        if "inventory" in data:
            for item_data in data["inventory"]:
                item = InventoryItem()
                item.pid = item_data.get("pid", 0)
                item.item_name = item_data.get("name", "")
                item.quantity = item_data.get("quantity", 1)
                item.condition = item_data.get("condition", 100)
                item.charges = item_data.get("charges", 0)
                item.is_equipped = item_data.get("is_equipped", False)
                npc.inventory.append(item)
        
        # Behavior
        if "behavior" in data:
            bhv = data["behavior"]
            npc.behavior.aggression = bhv.get("aggression", 0)
            npc.behavior.cowardice = bhv.get("cowardice", 0)
            npc.behavior.enthusiasm = bhv.get("enthusiasm", 50)
            npc.behavior.ai_number = bhv.get("ai_number", 0)
            npc.behavior.ai_package = AiPackage(bhv.get("ai_package", 0))
            npc.behavior.script_id = bhv.get("script_id", 0)
            npc.behavior.script_name = bhv.get("script_name", "")
            npc.behavior.movement_type = bhv.get("movement_type", "Walk")
            npc.behavior.run_distance = bhv.get("run_distance", 10)
            npc.behavior.combat_style = bhv.get("combat_style", "Default")
            npc.behavior.primary_weapon = bhv.get("primary_weapon", "")
            npc.behavior.secondary_weapon = bhv.get("secondary_weapon", "")
        
        # AI Settings
        if "ai_settings" in data:
            ai = data["ai_settings"]
            npc.ai_settings.brain_type = ai.get("brain_type", "Default")
            npc.ai_settings.packet_type = AiPackage(ai.get("packet_type", 0))
            npc.ai_settings.perception_radius = ai.get("perception_radius", 10)
            npc.ai_settings.vision_range = ai.get("vision_range", 10)
            npc.ai_settings.hearing_range = ai.get("hearing_range", 10)
            npc.ai_settings.attack_rate = ai.get("attack_rate", 3)
            npc.ai_settings.min_hit_chance = ai.get("min_hit_chance", 0)
            npc.ai_settings.max_distance = ai.get("max_distance", 15)
            npc.ai_settings.min_distance = ai.get("min_distance", 0)
            npc.ai_settings.wander_radius = ai.get("wander_radius", 5)
            npc.ai_settings.walk_speed = ai.get("walk_speed", 1.0)
            npc.ai_settings.run_speed = ai.get("run_speed", 2.0)
            npc.ai_settings.reaction_override = ai.get("reaction_override", -1)
            npc.ai_settings.fear_trigger = ai.get("fear_trigger", 25)
            npc.ai_settings.is_critical = ai.get("is_critical", False)
            npc.ai_settings.can_loot = ai.get("can_loot", True)
            npc.ai_settings.can_call_help = ai.get("can_call_help", True)
            npc.ai_settings.help_radius = ai.get("help_radius", 15)
            npc.ai_settings.team_id = ai.get("team_id", 0)
            npc.ai_settings.ai_group = ai.get("ai_group", 0)
        
        # Relationship
        if "relationship" in data:
            rel = data["relationship"]
            npc.relationship.relation_type = RelationshipType(rel.get("relation_type", 0))
            npc.relationship.relation_modifier = rel.get("relation_modifier", 0)
            npc.relationship.faction_id = rel.get("faction_id", 0)
            npc.relationship.faction_name = rel.get("faction_name", "")
            npc.relationship.faction_standing = rel.get("faction_standing", 0)
            npc.relationship.reputation = rel.get("reputation", 0)
            npc.relationship.reputation_type = ReputationType(rel.get("reputation_type", 0))
            npc.relationship.karma_level = rel.get("karma_level", "Neutral")
        
        # Dialogue
        if "dialogue" in data:
            dlg = data["dialogue"]
            npc.dialogue.dialogue_file = dlg.get("dialogue_file", "")
            npc.dialogue.default_node = dlg.get("default_node", "")
            npc.dialogue.greeting_node = dlg.get("greeting_node", "")
            npc.dialogue.trade_node = dlg.get("trade_node", "")
            npc.dialogue.death_node = dlg.get("death_node", "")
            npc.dialogue.knocked_out_node = dlg.get("knocked_out_node", "")
        
        return npc
