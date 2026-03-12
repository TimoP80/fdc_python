#!/usr/bin/env python3
"""
Debug script to test FMF parsing and UI updates
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.fmf_parser import FMFParser
from pathlib import Path

def test_parsing():
    print("Testing FMF parsing...")
    parser = FMFParser()
    dialogue = parser.load_from_file(Path('test_abraham.fmf'))

    print(f"Parsed dialogue with {dialogue.nodecount} nodes")
    print(f"NPC Name: {dialogue.npcname}")
    print(f"Total nodes: {len(dialogue.nodes)}")

    for i, node in enumerate(dialogue.nodes[:5]):  # Show first 5 nodes
        print(f"Node {i}: {node.nodename} - {len(node.options)} options")
        if node.options:
            print(f"  First option: {node.options[0].optiontext[:50]}...")

    return dialogue

if __name__ == "__main__":
    test_parsing()