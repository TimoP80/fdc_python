#!/usr/bin/env python
"""Test script for DDF export functionality"""

import sys
sys.path.insert(0, '.')

from core.ddf_output import DDFExporter, DDFOutputConfig
from models.dialogue import (
    Dialogue, DialogueNode, PlayerOption, 
    Reaction, Gender, SkillCheck, FloatNode
)

def create_test_dialogue():
    """Create a test dialogue for DDF export"""
    dialogue = Dialogue()
    dialogue.filename = 'test_dialogue.fmf'
    dialogue.npcname = 'Test NPC'
    dialogue.location = 'Test Location'
    dialogue.description = 'Test Description'
    dialogue.unknowndesc = 'Unknown description'
    dialogue.knowndesc = 'Known description'
    dialogue.detaileddesc = 'Detailed description'
    
    # Create a start node
    start_node = DialogueNode()
    start_node.nodename = 'Start'
    start_node.is_wtg = True
    start_node.npctext = 'Hello, traveler! What brings you here?'
    start_node.notes = 'Starting node'
    
    # Add player options
    option1 = PlayerOption(
        optiontext='I am looking for adventure.',
        nodelink='Adventure',
        reaction=Reaction.NEUTRAL,
        genderflags=Gender.NONE,
        intcheck=0
    )
    start_node.options.append(option1)
    start_node.optioncnt += 1
    
    option2 = PlayerOption(
        optiontext='Just passing through.',
        nodelink='done',
        reaction=Reaction.NEUTRAL,
        genderflags=Gender.NONE,
        intcheck=0
    )
    start_node.options.append(option2)
    start_node.optioncnt += 1
    
    dialogue.nodes.append(start_node)
    dialogue.nodecount += 1
    
    # Create another node
    adventure_node = DialogueNode()
    adventure_node.nodename = 'Adventure'
    adventure_node.npctext = 'Adventure? There is plenty of that here!'
    
    option3 = PlayerOption(
        optiontext='Good to know. Goodbye.',
        nodelink='done',
        reaction=Reaction.GOOD,
        genderflags=Gender.NONE,
        intcheck=0
    )
    adventure_node.options.append(option3)
    adventure_node.optioncnt += 1
    
    dialogue.nodes.append(adventure_node)
    dialogue.nodecount += 1
    
    return dialogue

def main():
    print("Testing DDF Export...")
    
    # Create test dialogue
    dialogue = create_test_dialogue()
    print(f"Created dialogue: {dialogue.npcname} with {dialogue.nodecount} nodes")
    
    # Configure DDF export
    config = DDFOutputConfig()
    config.ssl_path = "output/ssl"
    config.msg_path = "output/msg"
    config.template_path = "templates/basic.txt"
    
    # Export to DDF
    exporter = DDFExporter(config)
    output_lines = exporter.export_to_ddf(dialogue)
    
    print(f"Generated {len(output_lines)} lines of DDF output")
    
    # Print output
    print("\n=== DDF Output ===")
    for line in output_lines:
        print(line)
    
    # Write to file
    output_file = "test_output.ddf"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"\nWrote output to {output_file}")
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()
