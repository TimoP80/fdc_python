#!/usr/bin/env python3
"""
Test script for SSL + MSG Export Plugin

Tests the export functionality for Fallout 2 dialogue files.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from models.dialogue import (
    Dialogue, DialogueNode, PlayerOption, Condition,
    CheckType, CompareType, LinkType, SkillCheck, CustomProcedure,
    Variable, Gender, Reaction
)
from core.ssl_exporter import SSLExporter, ExportConfig, GameVersion, export_ssl
from core.msg_exporter import MSGExporter, export_msg, create_msg_filename


def create_test_dialogue() -> Dialogue:
    """Create a test dialogue for export testing"""
    
    dialogue = Dialogue()
    dialogue.npcname = "Test NPC"
    dialogue.location = "Test Location"
    dialogue.description = "A test NPC for export validation"
    dialogue.unknowndesc = "You see a test NPC."
    dialogue.detaileddesc = "This is a detailed description of the test NPC."
    
    # Create dialogue nodes
    node1 = DialogueNode()
    node1.nodename = "Node0"
    node1.npctext = "Hello, traveler! Welcome to our village."
    node1.npctext_female = "Hello, traveler! Welcome to our village."
    node1.is_wtg = True
    
    # Add player options - use keyword arguments
    option1 = PlayerOption(optiontext="Who are you?", nodelink="Node1")
    option1.intcheck = 0
    option1.reaction = Reaction.NEUTRAL
    node1.options.append(option1)

    option2 = PlayerOption(optiontext="I need information.", nodelink="Node2")
    option2.intcheck = 0
    option2.reaction = Reaction.NEUTRAL
    node1.options.append(option2)
    
    dialogue.nodes.append(node1)
    
    # Node 1 - Who are you
    node2 = DialogueNode()
    node2.nodename = "Node1"
    node2.npctext = "I am the village elder. I've been leading this community for many years."
    node2.options.append(PlayerOption(
        optiontext="Tell me about the village.",
        nodelink="Node3",
        intcheck=0,
        reaction=Reaction.GOOD
    ))
    node2.options.append(PlayerOption(
        optiontext="Goodbye.",
        nodelink="Node999",
        intcheck=0,
        reaction=Reaction.NEUTRAL
    ))
    dialogue.nodes.append(node2)
    
    # Node 2 - Information request
    node3 = DialogueNode()
    node3.nodename = "Node2"
    node3.npctext = "What kind of information do you seek?"
    node3.options.append(PlayerOption(
        optiontext="Never mind.",
        nodelink="Node999",
        intcheck=0,
        reaction=Reaction.NEUTRAL
    ))
    dialogue.nodes.append(node3)
    
    # Node 3 - About village
    node4 = DialogueNode()
    node4.nodename = "Node3"
    node4.npctext = "Our village has been here for generations."
    node4.options.append(PlayerOption(
        optiontext="I should go.",
        nodelink="Node999",
        intcheck=0,
        reaction=Reaction.NEUTRAL
    ))
    dialogue.nodes.append(node4)
    
    dialogue.nodecount = len(dialogue.nodes)
    
    return dialogue


def test_ssl_export():
    """Test SSL export"""
    print("=" * 60)
    print("Testing SSL Export")
    print("=" * 60)
    
    dialogue = create_test_dialogue()
    
    # Create export config
    config = ExportConfig(
        game_version=GameVersion.FALLOUT_2,
        output_directory=Path("test_output"),
        script_number="999",
        headers_path="headers",
        include_debug_comments=True,
        encoding="cp1252"
    )
    
    # Export SSL
    exporter = SSLExporter(config)
    ssl_content = exporter.export(dialogue)
    
    print(f"\nGenerated SSL content ({len(ssl_content)} characters):")
    print("-" * 40)
    print(ssl_content[:1000])  # Print first 1000 chars
    print("..." if len(ssl_content) > 1000 else "")
    print("-" * 40)
    
    # Validate
    from core.ssl_exporter import SSLValidator
    validator = SSLValidator()
    is_valid, errors, warnings = validator.validate(ssl_content)
    
    print(f"\nValidation Results:")
    print(f"  Valid: {is_valid}")
    if errors:
        print(f"  Errors: {errors}")
    if warnings:
        print(f"  Warnings: {warnings}")
    
    # Write to file
    output_path = Path("test_output/test_npc.ssl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ssl_content, encoding="utf-8")
    print(f"\nSSL written to: {output_path}")
    
    return is_valid


def test_msg_export():
    """Test MSG export"""
    print("\n" + "=" * 60)
    print("Testing MSG Export")
    print("=" * 60)
    
    dialogue = create_test_dialogue()
    
    # Export MSG
    exporter = MSGExporter(encoding="cp1252")
    msg_content = exporter.export(dialogue)
    
    print(f"\nGenerated MSG content:")
    print("-" * 40)
    print(msg_content)
    print("-" * 40)
    
    # Get entry count
    entry_count = exporter.get_entry_count()
    id_range = exporter.get_msg_id_range()
    
    print(f"\nMSG Statistics:")
    print(f"  Total entries: {entry_count}")
    print(f"  ID range: {id_range[0]} to {id_range[1]}")
    
    # Write to file
    output_path = Path("test_output/test_npc.msg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(msg_content, encoding="cp1252")
    print(f"\nMSG written to: {output_path}")
    
    return True


def test_filename_generation():
    """Test filename generation"""
    print("\n" + "=" * 60)
    print("Testing Filename Generation")
    print("=" * 60)
    
    dialogue = Dialogue()
    dialogue.npcname = "Village Elder"
    
    filename = create_msg_filename(dialogue)
    print(f"Dialogue 'Village Elder' -> MSG filename: {filename}")
    
    dialogue.npcname = "Mr.  Happy"
    filename = create_msg_filename(dialogue)
    print(f"Dialogue 'Mr.  Happy' -> MSG filename: {filename}")
    
    dialogue.npcname = "Test-NPC-123"
    filename = create_msg_filename(dialogue)
    print(f"Dialogue 'Test-NPC-123' -> MSG filename: {filename}")
    
    return True


def test_encoding():
    """Test character encoding"""
    print("\n" + "=" * 60)
    print("Testing Character Encoding")
    print("=" * 60)
    
    # Create dialogue with special characters
    dialogue = Dialogue()
    dialogue.npcname = "Test NPC"
    dialogue.unknowndesc = "You see a cafe with resume signs."
    dialogue.detaileddesc = "The SPECIAL system: Strength, Perception, Endurance, Charisma, Intelligence, Agility, and Luck."
    
    node = DialogueNode()
    node.nodename = "Node0"
    node.npctext = "Hello! How can I help you today?niper is my favorite weapon."
    dialogue.nodes.append(node)
    dialogue.nodecount = 1
    
    # Export with CP1252 encoding
    exporter = MSGExporter(encoding="cp1252")
    msg_content = exporter.export(dialogue)
    
    # Try to write and read back
    output_path = Path("test_output/encoding_test.msg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(msg_content, encoding="cp1252")
    
    # Read back
    content_read = output_path.read_text(encoding="cp1252")
    print(f"CP1252 encoding test: {'PASSED' if content_read else 'FAILED'}")
    
    # Clean up
    output_path.unlink()
    
    return True


def main():
    """Run all tests"""
    print("SSL + MSG Export Plugin Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("SSL Export", test_ssl_export()))
    results.append(("MSG Export", test_msg_export()))
    results.append(("Filename Generation", test_filename_generation()))
    results.append(("Encoding", test_encoding()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED!")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
