"""
GUI Texture Generator - Fast Version
Generates and saves pre-generated textures for GUI components to assets folder.
Optimized for faster generation with smaller dimensions.
"""

import os
import sys
import time

# Add the src directory to path to import the texture system
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.texture_system import (
    TextureGenerator, TextureStyle, ResolutionVariant
)


def save_texture(texture, filepath):
    """Save a QPixmap texture to a file."""
    if texture and not texture.isNull():
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        texture.save(filepath, "PNG")
        return True
    return False


def generate_fast_textures():
    """Generate textures with optimized settings."""
    print("=" * 60)
    print("GUI Texture Generator - Fast Version")
    print("=" * 60)
    
    # Check for QApplication
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            print("\nCreating QApplication...")
            app = QApplication(sys.argv)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    start_time = time.time()
    generated_count = 0
    
    # ==================== PANELS ====================
    print("\n=== Generating Panel Textures ===")
    panels = [
        # (name, width, height, generator_func, args)
        ("panels/metal_steel", 256, 256, TextureGenerator.generate_metal_texture, {"metal_type": "steel", "scratches": False}),
        ("panels/metal_copper", 256, 256, TextureGenerator.generate_metal_texture, {"metal_type": "copper", "scratches": True}),
        ("panels/metal_rust", 256, 256, TextureGenerator.generate_metal_texture, {"metal_type": "rust", "scratches": True}),
        ("panels/wood_oak", 256, 256, TextureGenerator.generate_wood_texture, {"wood_type": "oak", "scale": 10.0}),
        ("panels/wood_pine", 256, 256, TextureGenerator.generate_wood_texture, {"wood_type": "pine", "scale": 10.0}),
        ("panels/concrete_dirty", 256, 256, TextureGenerator.generate_concrete_texture, {"dirty": True}),
        ("panels/rust_heavy", 256, 256, TextureGenerator.generate_rust_texture, {"intensity": 0.9}),
        ("panels/leather_brown", 256, 256, TextureGenerator.generate_leather_texture, {"leather_type": "brown", "worn": True}),
        ("panels/glass_clear", 256, 256, TextureGenerator.generate_glass_texture, {"glass_type": "clear", "frosted": False}),
        ("panels/glass_frosted", 256, 256, TextureGenerator.generate_glass_texture, {"glass_type": "clear", "frosted": True}),
        ("panels/carbon_fiber", 256, 256, TextureGenerator.generate_carbon_fiber_texture, {"clear_coat": True}),
    ]
    
    for name, w, h, gen_func, kwargs in panels:
        print(f"  Generating {name}...")
        texture = gen_func(w, h, seed=42, **kwargs)
        if save_texture(texture, f"assets/{name}.png"):
            generated_count += 1
    
    # ==================== BUTTONS ====================
    print("\n=== Generating Button Textures ===")
    buttons = [
        ("buttons/wood_oak", 256, 128, TextureGenerator.generate_wood_texture, {"wood_type": "oak", "scale": 12.0}),
        ("buttons/metal_steel", 256, 128, TextureGenerator.generate_metal_texture, {"metal_type": "steel", "scratches": True}),
        ("buttons/metal_copper", 256, 128, TextureGenerator.generate_metal_texture, {"metal_type": "copper", "scratches": True}),
        ("buttons/rust_standard", 256, 128, TextureGenerator.generate_rust_texture, {"intensity": 0.8}),
        ("buttons/leather_brown", 256, 128, TextureGenerator.generate_leather_texture, {"leather_type": "brown", "worn": True}),
        ("buttons/plastic_white", 256, 128, TextureGenerator.generate_plastic_texture, {"plastic_type": "white", "glossy": True}),
        ("buttons/plastic_black", 256, 128, TextureGenerator.generate_plastic_texture, {"plastic_type": "black", "glossy": True}),
        ("buttons/plastic_red", 256, 128, TextureGenerator.generate_plastic_texture, {"plastic_type": "red", "glossy": True}),
        ("buttons/plastic_blue", 256, 128, TextureGenerator.generate_plastic_texture, {"plastic_type": "blue", "glossy": True}),
        ("buttons/plastic_green", 256, 128, TextureGenerator.generate_plastic_texture, {"plastic_type": "green", "glossy": True}),
        ("buttons/neumorphic_light", 256, 128, TextureGenerator.generate_neumorphic_texture, {"style": "light", "convex": True}),
        ("buttons/neumorphic_pressed", 256, 128, TextureGenerator.generate_neumorphic_texture, {"style": "light", "convex": False}),
    ]
    
    for name, w, h, gen_func, kwargs in buttons:
        print(f"  Generating {name}...")
        texture = gen_func(w, h, seed=42, **kwargs)
        if save_texture(texture, f"assets/{name}.png"):
            generated_count += 1
    
    # ==================== BORDERS ====================
    print("\n=== Generating Border Textures ===")
    borders = [
        ("borders/metal_steel_h", 64, 8, TextureGenerator.generate_metal_texture, {"metal_type": "steel", "scratches": False}),
        ("borders/metal_steel_v", 8, 64, TextureGenerator.generate_metal_texture, {"metal_type": "steel", "scratches": False}),
        ("borders/rust_h", 64, 8, TextureGenerator.generate_rust_texture, {"intensity": 0.7}),
        ("borders/wood_h", 64, 8, TextureGenerator.generate_wood_texture, {"wood_type": "oak", "scale": 8.0}),
        ("borders/corner_metal", 16, 16, TextureGenerator.generate_metal_texture, {"metal_type": "steel", "scratches": True}),
    ]
    
    for name, w, h, gen_func, kwargs in borders:
        print(f"  Generating {name}...")
        texture = gen_func(w, h, seed=42, **kwargs)
        if save_texture(texture, f"assets/{name}.png"):
            generated_count += 1
    
    # ==================== BACKGROUNDS ====================
    print("\n=== Generating Background Textures ===")
    backgrounds = [
        ("backgrounds/gradient_dark", 256, 256, TextureGenerator.generate_gradient_texture, {"gradient_type": "dark", "direction": "vertical", "grain": 0.03}),
        ("backgrounds/gradient_midnight", 256, 256, TextureGenerator.generate_gradient_texture, {"gradient_type": "midnight", "direction": "diagonal", "grain": 0.04}),
        ("backgrounds/tech_circuit_green", 256, 256, TextureGenerator.generate_tech_pattern, {"pattern_type": "circuit", "color_scheme": "green", "glow": True}),
        ("backgrounds/tech_grid_dark", 256, 256, TextureGenerator.generate_tech_pattern, {"pattern_type": "grid", "color_scheme": "dark", "glow": True}),
        ("backgrounds/holographic_rainbow", 256, 256, TextureGenerator.generate_holographic_texture, {"holo_type": "rainbow", "intensity": 0.6}),
        ("backgrounds/dark_mode", 256, 256, TextureGenerator.generate_dark_mode_texture, {"accent_color": None}),
        ("backgrounds/dark_mode_blue", 256, 256, TextureGenerator.generate_dark_mode_texture, {"accent_color": "blue"}),
    ]
    
    for name, w, h, gen_func, kwargs in backgrounds:
        print(f"  Generating {name}...")
        texture = gen_func(w, h, seed=42, **kwargs)
        if save_texture(texture, f"assets/{name}.png"):
            generated_count += 1
    
    # ==================== TILED ====================
    print("\n=== Generating Tiled Textures ===")
    tiled = [
        ("tiled/metal_steel_64", 64, 64, TextureGenerator.generate_metal_texture, {"metal_type": "steel", "scratches": True}),
        ("tiled/metal_copper_64", 64, 64, TextureGenerator.generate_metal_texture, {"metal_type": "copper", "scratches": True}),
        ("tiled/rust_64", 64, 64, TextureGenerator.generate_rust_texture, {"intensity": 0.7}),
        ("tiled/wood_oak_64", 64, 64, TextureGenerator.generate_wood_texture, {"wood_type": "oak", "scale": 8.0}),
        ("tiled/concrete_64", 64, 64, TextureGenerator.generate_concrete_texture, {"dirty": True}),
    ]
    
    for name, w, h, gen_func, kwargs in tiled:
        print(f"  Generating {name}...")
        texture = gen_func(w, h, seed=42, **kwargs)
        if save_texture(texture, f"assets/{name}.png"):
            generated_count += 1
    
    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"Generation complete!")
    print(f"  Generated: {generated_count} textures")
    print(f"  Time: {elapsed:.1f} seconds")
    print(f"{'=' * 60}")
    
    # List files
    print("\nGenerated files:")
    for root, dirs, files in os.walk("assets"):
        for file in sorted(files):
            if file.endswith(".png"):
                filepath = os.path.join(root, file)
                size = os.path.getsize(filepath)
                print(f"  {filepath} ({size:,} bytes)")


if __name__ == "__main__":
    generate_fast_textures()
