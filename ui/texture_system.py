"""
Texture System Module
Provides procedural texture generation with realistic surface materials
and bump mapping for the Fallout Dialogue Creator GUI.

Features:
- Procedural texture generation (wood grain, metal, leather, concrete, rust)
- Texture caching for performance
- Normal map generation for 3D depth effect
- Seamless tiling support
"""

import math
import random
from typing import Dict, Tuple, Optional
from functools import lru_cache

from PyQt6.QtGui import (
    QImage, QPixmap, QColor, QPainter, QBrush, QLinearGradient,
    QRadialGradient, QConicalGradient
)
from PyQt6.QtCore import Qt, QSize, QRect


# =============================================================================
# PROCEDURAL NOISE FUNCTIONS
# =============================================================================

def _fade(t: float) -> float:
    """Smoothstep fade function for Perlin noise"""
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation"""
    return a + t * (b - a)


def _grad(hash_val: int, x: float, y: float) -> float:
    """Gradient function for Perlin noise"""
    h = hash_val & 3
    u = x if h < 2 else y
    v = y if h < 2 else x
    return (u if h & 1 == 0 else -u) + (v if h & 2 == 0 else -v)


def _perlin_noise(x: float, y: float, seed: int = 0) -> float:
    """
    Generate Perlin noise value at coordinates.
    Uses a deterministic permutation table based on seed.
    """
    # Create a deterministic permutation table based on seed
    # Use a separate random generator for the permutation to avoid affecting global state
    rng = random.Random(seed)
    
    # Create pseudo-random permutation table
    perm = list(range(256))
    rng.shuffle(perm)
    perm = perm * 2
    
    xi = int(math.floor(x)) & 255
    yi = int(math.floor(y)) & 255
    
    xf = x - math.floor(x)
    yf = y - math.floor(y)
    
    u = _fade(xf)
    v = _fade(yf)
    
    aa = perm[perm[xi] + yi]
    ab = perm[perm[xi] + yi + 1]
    ba = perm[perm[xi + 1] + yi]
    bb = perm[perm[xi + 1] + yi + 1]
    
    x1 = _lerp(_grad(aa, xf, yf), _grad(ba, xf - 1, yf), u)
    x2 = _lerp(_grad(ab, xf, yf - 1), _grad(bb, xf - 1, yf - 1), u)
    
    return (_lerp(x1, x2, v) + 1) / 2  # Normalize to 0-1


def fbm_noise(x: float, y: float, octaves: int = 4, 
              persistence: float = 0.5, seed: int = 0) -> float:
    """
    Fractal Brownian Motion - layered noise for natural textures
    """
    total = 0
    frequency = 1
    amplitude = 1
    max_value = 0
    
    for _ in range(octaves):
        total += _perlin_noise(x * frequency, y * frequency, seed) * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= 2
    
    return total / max_value


def voronoi_noise(x: float, y: float, seed: int = 0) -> Tuple[float, int]:
    """
    Voronoi/Worley noise for cellular patterns (useful for cracks, tiles)
    Returns (distance, cell_id)
    """
    # Use a local random generator for deterministic results
    rng = random.Random(seed)
    
    xi = int(math.floor(x))
    yi = int(math.floor(y))
    
    min_dist = float('inf')
    closest_cell = 0
    
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            cell_x = xi + dx
            cell_y = yi + dy
            
            # Create a seeded random generator for this cell
            cell_rng = random.Random(cell_x * 374761393 + cell_y * 668265263 + seed)
            point_x = cell_x + cell_rng.random()
            point_y = cell_y + cell_rng.random()
            
            dist = math.sqrt((x - point_x) ** 2 + (y - point_y) ** 2)
            
            if dist < min_dist:
                min_dist = dist
                closest_cell = cell_x * 1000 + cell_y
    
    return min_dist, closest_cell


# =============================================================================
# TEXTURE COLOR PALETTES
# =============================================================================

class TextureColors:
    """Color definitions for various texture types"""
    
    # Wood colors
    WOOD_OAK = {"base": (139, 90, 43), "dark": (101, 67, 33), "light": (205, 133, 63)}
    WOOD_PINE = {"base": (160, 120, 70), "dark": (120, 90, 50), "light": (200, 160, 100)}
    WOOD_WALNUT = {"base": (77, 51, 33), "dark": (51, 33, 20), "light": (120, 80, 50)}
    
    # Metal colors
    METAL_STEEL = {"base": (128, 128, 130), "light": (180, 180, 185), "dark": (80, 80, 85)}
    METAL_COPPER = {"base": (184, 115, 51), "light": (217, 155, 76), "dark": (139, 80, 31)}
    METAL_RUST = {"base": (150, 70, 30), "light": (180, 90, 40), "dark": (100, 40, 20)}
    METAL_BRASS = {"base": (181, 166, 66), "light": (212, 199, 99), "dark": (139, 125, 45)}
    
    # Leather colors
    LEATHER_BROWN = {"base": (101, 67, 33), "light": (139, 100, 55), "dark": (65, 40, 18)}
    LEATHER_DARK = {"base": (45, 30, 20), "light": (70, 50, 35), "dark": (25, 15, 10)}
    LEATHER_TAN = {"base": (210, 180, 140), "light": (230, 200, 160), "dark": (160, 130, 90)}
    
    # Concrete colors
    CONCRETE_GRAY = {"base": (140, 140, 140), "light": (180, 180, 180), "dark": (100, 100, 100)}
    CONCRETE_DIRTY = {"base": (120, 115, 105), "light": (150, 145, 135), "dark": (90, 85, 75)}
    
    # Worn surface colors
    WORN_METAL = {"base": (100, 100, 100), "light": (140, 140, 140), "dark": (60, 60, 60)}
    WORN_PAINT = {"base": (80, 90, 70), "light": (110, 120, 90), "dark": (50, 60, 40)}
    
    # Plastic colors
    PLASTIC_WHITE = {"base": (245, 245, 245), "light": (255, 255, 255), "dark": (220, 220, 220)}
    PLASTIC_BLACK = {"base": (30, 30, 30), "light": (50, 50, 50), "dark": (15, 15, 15)}
    PLASTIC_RED = {"base": (200, 40, 40), "light": (230, 80, 80), "dark": (140, 20, 20)}
    PLASTIC_BLUE = {"base": (40, 80, 180), "light": (80, 120, 220), "dark": (20, 50, 140)}
    PLASTIC_GREEN = {"base": (40, 160, 60), "light": (80, 200, 100), "dark": (20, 120, 30)}
    PLASTIC_ORANGE = {"base": (255, 140, 0), "light": (255, 180, 50), "dark": (200, 100, 0)}
    
    # Glass colors
    GLASS_CLEAR = {"base": (200, 220, 240), "light": (255, 255, 255), "dark": (150, 170, 190)}
    GLASS_TINTED = {"base": (60, 80, 100), "light": (100, 120, 150), "dark": (30, 40, 60)}
    GLASS_AMBER = {"base": (255, 190, 80), "light": (255, 220, 130), "dark": (180, 130, 50)}
    GLASS_GREEN = {"base": (80, 160, 120), "light": (130, 200, 160), "dark": (50, 120, 80)}
    
    # Carbon fiber colors
    CARBON_WEAVE = {"base": (30, 30, 35), "light": (60, 60, 70), "dark": (15, 15, 20)}
    CARBON_CLEAR = {"base": (40, 45, 50), "light": (70, 75, 85), "dark": (20, 22, 25)}
    
    # Fabric colors
    FABRIC_CANVAS = {"base": (200, 195, 180), "light": (230, 225, 210), "dark": (160, 155, 140)}
    FABRIC_DENIM = {"base": (70, 90, 130), "light": (100, 120, 160), "dark": (50, 65, 100)}
    FABRIC_Tweed = {"base": (100, 90, 80), "light": (140, 130, 120), "dark": (70, 60, 50)}
    FABRIC_Velvet = {"base": (80, 50, 80), "light": (120, 80, 120), "dark": (50, 30, 50)}
    FABRIC_CarbonWeave = {"base": (45, 50, 55), "light": (75, 80, 90), "dark": (25, 28, 32)}
    
    # Gradient backgrounds
    GRADIENT_DARK = {"base": (20, 20, 25), "light": (40, 40, 50), "dark": (10, 10, 15)}
    GRADIENT_MIDNIGHT = {"base": (20, 30, 60), "light": (40, 60, 100), "dark": (10, 15, 40)}
    GRADIENT_SUNSET = {"base": (80, 40, 60), "light": (140, 80, 100), "dark": (40, 20, 30)}
    GRADIENT_FOREST = {"base": (30, 60, 40), "light": (60, 100, 70), "dark": (15, 40, 20)}
    
    # Holographic colors
    HOLOGRAPHIC_RAINBOW = {"base": (128, 128, 192), "light": (192, 192, 255), "dark": (64, 64, 128)}
    HOLOGRAPHIC_SILVER = {"base": (180, 185, 200), "light": (220, 225, 240), "dark": (140, 145, 160)}
    HOLOGRAPHIC_GOLD = {"base": (200, 170, 80), "light": (255, 220, 130), "dark": (150, 120, 50)}
    
    # Tech/Circuit colors
    TECH_CIRCUIT_GREEN = {"base": (30, 50, 30), "light": (60, 100, 60), "dark": (15, 30, 15)}
    TECH_CIRCUIT_BLUE = {"base": (30, 40, 60), "light": (60, 80, 120), "dark": (15, 20, 40)}
    TECH_CIRCUIT_CYAN = {"base": (30, 60, 70), "light": (60, 120, 140), "dark": (15, 40, 50)}
    TECH_GRID_DARK = {"base": (25, 25, 30), "light": (50, 50, 60), "dark": (10, 10, 15)}
    
    # Neumorphic colors
    NEUMORPHIC_LIGHT = {"base": (230, 230, 235), "light": (255, 255, 255), "dark": (200, 200, 210)}
    NEUMORPHIC_DARK = {"base": (45, 45, 50), "light": (70, 70, 80), "dark": (25, 25, 30)}
    NEUMORPHIC_BLUE = {"base": (60, 80, 120), "light": (90, 110, 150), "dark": (40, 55, 90)}
    
    # High contrast colors (accessibility)
    HIGH_CONTRAST_DARK = {"base": (0, 0, 0), "light": (60, 60, 60), "dark": (0, 0, 0)}
    HIGH_CONTRAST_LIGHT = {"base": (255, 255, 255), "light": (255, 255, 255), "dark": (200, 200, 200)}
    HIGH_CONTRAST_YELLOW = {"base": (255, 220, 0), "light": (255, 255, 100), "dark": (200, 170, 0)}
    HIGH_CONTRAST_CYAN = {"base": (0, 180, 180), "light": (100, 220, 220), "dark": (0, 130, 130)}


# =============================================================================
# TEXTURE GENERATOR CLASS
# =============================================================================

class TextureGenerator:
    """
    Procedural texture generator with caching.
    Generates realistic surface textures for UI elements.
    """
    
    # Cache for generated textures
    _texture_cache: Dict[str, QPixmap] = {}
    _normal_map_cache: Dict[str, QPixmap] = {}
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached textures"""
        cls._texture_cache.clear()
        cls._normal_map_cache.clear()
    
    @classmethod
    def _generate_fallback_texture(cls, width: int, height: int, color: Tuple[int, int, int] = (128, 128, 128)) -> QPixmap:
        """
        Generate a simple solid color fallback texture.
        Used when procedural texture generation fails.
        """
        try:
            if not _ensure_qapplication():
                return QPixmap()
            
            pixmap = QPixmap(width, height)
            pixmap.fill(QColor(*color))
            return pixmap
        except Exception:
            return QPixmap()
    
    @classmethod
    def generate_wood_texture(cls, width: int, height: int, 
                              wood_type: str = "oak",
                              scale: float = 8.0,
                              seed: int = 42) -> QPixmap:
        """
        Generate realistic wood grain texture.
        
        Args:
            width, height: Texture dimensions
            wood_type: "oak", "pine", or "walnut"
            scale: Grain scale (higher = finer grain)
            seed: Random seed for reproducibility
        """
        # Check for QApplication
        if not _ensure_qapplication():
            return QPixmap()
        
        try:
            cache_key = f"wood_{wood_type}_{width}x{height}_{scale}_{seed}"
            
            if cache_key in cls._texture_cache:
                return cls._texture_cache[cache_key]
            
            palette = getattr(TextureColors, f"WOOD_{wood_type.upper()}", TextureColors.WOOD_OAK)
            
            image = QImage(width, height, QImage.Format.Format_RGB32)
            
            # Use a local random generator for color variation
            variation_rng = random.Random(seed + 500)
            
            for y in range(height):
                for x in range(width):
                    # Generate wood grain pattern
                    nx = x / scale
                    ny = y / scale * 0.3  # Stretch vertically for grain effect
                    
                    # Combine noise for wood grain
                    grain = fbm_noise(nx, ny, octaves=4, seed=seed)
                    
                    # Add ring pattern
                    ring_noise = math.sin(ny * 20 + grain * 5) * 0.5 + 0.5
                    
                    # Add knots occasionally
                    knot_dist = voronoi_noise(nx * 0.5, ny * 0.5, seed + 100)[0]
                    knot = 1.0 - min(1.0, knot_dist * 3) if knot_dist < 0.3 else 0
                    
                    # Blend colors based on pattern
                    base_color = list(palette["base"])
                    dark_color = palette["dark"]
                    light_color = palette["light"]
                    
                    # Apply grain
                    if knot > 0:
                        # Knot area - darker
                        blend = knot * 0.8 + grain * 0.2
                        final_color = [
                            int(dark_color[0] * (1 - blend) + base_color[0] * blend),
                            int(dark_color[1] * (1 - blend) + base_color[1] * blend),
                            int(dark_color[2] * (1 - blend) + base_color[2] * blend)
                        ]
                    else:
                        # Normal grain
                        blend = ring_noise * 0.3 + grain * 0.4
                        if blend > 0.6:
                            final_color = light_color
                        elif blend < 0.4:
                            final_color = dark_color
                        else:
                            final_color = base_color
                    
                    # Add subtle color variation using deterministic random
                    variation = (variation_rng.random() - 0.5) * 10
                    final_color = [
                        max(0, min(255, final_color[0] + int(variation))),
                        max(0, min(255, final_color[1] + int(variation))),
                        max(0, min(255, final_color[2] + int(variation)))
                    ]
                    
                    image.setPixelColor(x, y, QColor(*final_color))
            
            pixmap = QPixmap.fromImage(image)
            cls._texture_cache[cache_key] = pixmap
            return pixmap
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error generating wood texture: {e}")
            # Return a simple fallback texture
            return cls._generate_fallback_texture(width, height, (139, 90, 43))
    
    @classmethod
    def generate_metal_texture(cls, width: int, height: int,
                                metal_type: str = "steel",
                                scratches: bool = True,
                                seed: int = 42) -> QPixmap:
        """
        Generate realistic metal texture with scratches and wear.
        
        Args:
            width, height: Texture dimensions
            metal_type: "steel", "copper", "rust", or "brass"
            scratches: Include scratch marks
            seed: Random seed for reproducibility
        """
        # Check for QApplication
        if not _ensure_qapplication():
            return QPixmap()
        
        try:
            cache_key = f"metal_{metal_type}_{width}x{height}_{scratches}_{seed}"
            
            if cache_key in cls._texture_cache:
                return cls._texture_cache[cache_key]
            
            palette = getattr(TextureColors, f"METAL_{metal_type.upper()}", TextureColors.METAL_STEEL)
            
            image = QImage(width, height, QImage.Format.Format_RGB32)
            
            # Use a local random generator for scratches
            scratch_rng = random.Random(seed + 1000)
            
            # Generate base metal with brushed metal effect
            for y in range(height):
                for x in range(width):
                    # Brushed metal lines
                    brushed = math.sin(x * 0.5 + y * 0.1) * 0.5 + 0.5
                    
                    # Add noise for texture
                    noise_val = fbm_noise(x / 20, y / 20, octaves=3, seed=seed)
                    
                    # Scratches
                    scratch = 0
                    if scratches:
                        scratch_seed = int(x * 0.1) * 1000 + int(y * 0.1)
                        # Use deterministic random for scratches
                        cell_rng = random.Random(scratch_seed + seed)
                        if cell_rng.random() < 0.02:
                            # Create scratch
                            scratch = cell_rng.random() * 0.3
                    
                    # Combine effects
                    base = palette["base"]
                    light = palette["light"]
                    dark = palette["dark"]
                    
                    blend = noise_val * 0.4 + brushed * 0.3 + scratch
                    
                    if blend > 0.6:
                        color = light
                    elif blend < 0.4:
                        color = dark
                    else:
                        color = base
                    
                    # Add metallic sheen
                    sheen = math.sin(x * 0.1 + y * 0.05) * 0.1
                    
                    final_color = [
                        max(0, min(255, int(color[0] + sheen * 30))),
                        max(0, min(255, int(color[1] + sheen * 30))),
                        max(0, min(255, int(color[2] + sheen * 30)))
                    ]
                    
                    image.setPixelColor(x, y, QColor(*final_color))
            
            pixmap = QPixmap.fromImage(image)
            cls._texture_cache[cache_key] = pixmap
            return pixmap
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error generating metal texture: {e}")
            # Return a simple fallback texture
            return cls._generate_fallback_texture(width, height, (128, 128, 130))
    
    @classmethod
    def generate_rust_texture(cls, width: int, height: int,
                               intensity: float = 0.7,
                               seed: int = 42) -> QPixmap:
        """
        Generate realistic rust texture with patches and variation.
        """
        # Check for QApplication
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"rust_{width}x{height}_{intensity}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        rust_colors = [
            (180, 90, 40),   # Light rust
            (150, 70, 30),   # Medium rust
            (120, 50, 25),   # Dark rust
            (90, 35, 20),    # Deep rust
        ]
        
        base_metal = (100, 100, 105)
        
        for y in range(height):
            for x in range(width):
                # Multiple layers of rust pattern
                rust1 = voronoi_noise(x / 30, y / 30, seed)[0]
                rust2 = voronoi_noise(x / 60 + 100, y / 60 + 100, seed + 50)[0]
                noise = fbm_noise(x / 15, y / 15, octaves=3, seed=seed + 100)
                
                # Determine rust amount
                rust_amount = (rust1 * 0.5 + rust2 * 0.3 + noise * 0.2) * intensity
                
                if rust_amount < 0.3:
                    # Bare metal with some staining
                    stain = noise * 0.2
                    color = [
                        int(base_metal[0] * (1 - stain)),
                        int(base_metal[1] * (1 - stain)),
                        int(base_metal[2] * (1 - stain))
                    ]
                else:
                    # Rust coloring
                    rust_idx = min(3, int(rust_amount * 4))
                    color = list(rust_colors[rust_idx])
                    
                    # Add some variation
                    var = (random.random() - 0.5) * 20
                    color = [
                        max(0, min(255, color[0] + int(var))),
                        max(0, min(255, color[1] + int(var))),
                        max(0, min(255, color[2] + int(var)))
                    ]
                
                image.setPixelColor(x, y, QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_leather_texture(cls, width: int, height: int,
                                  leather_type: str = "brown",
                                  worn: bool = True,
                                  seed: int = 42) -> QPixmap:
        """
        Generate realistic leather texture with grain and wear.
        """
        # Check for QApplication
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"leather_{leather_type}_{width}x{height}_{worn}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = getattr(TextureColors, f"LEATHER_{leather_type.upper()}", TextureColors.LEATHER_BROWN)
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        for y in range(height):
            for x in range(width):
                # Leather grain pattern
                grain = voronoi_noise(x / 8, y / 8, seed)[0]
                noise = fbm_noise(x / 25, y / 25, octaves=4, seed=seed)
                
                # Worn edges effect
                worn_effect = 0
                if worn:
                    edge_dist = min(x, y, width - x, height - y) / 50
                    worn_effect = max(0, 1 - edge_dist) * 0.3
                
                # Base color
                base = palette["base"]
                dark = palette["dark"]
                light = palette["light"]
                
                blend = grain * 0.3 + noise * 0.4 + worn_effect
                
                if blend > 0.65:
                    color = light
                elif blend < 0.35:
                    color = dark
                else:
                    color = base
                
                # Add subtle creases
                crease = math.sin(x * 0.3 + y * 0.2) * 0.5 + 0.5
                crease = crease * 0.1 if crease > 0.7 else 0
                
                final_color = [
                    max(0, min(255, int(color[0] - crease * 30))),
                    max(0, min(255, int(color[1] - crease * 30))),
                    max(0, min(255, int(color[2] - crease * 30)))
                ]
                
                image.setPixelColor(x, y, QColor(*final_color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_concrete_texture(cls, width: int, height: int,
                                   dirty: bool = True,
                                   seed: int = 42) -> QPixmap:
        """
        Generate realistic concrete texture with cracks and dirt.
        """
        # Check for QApplication
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"concrete_{width}x{height}_{dirty}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = TextureColors.CONCRETE_DIRTY if dirty else TextureColors.CONCRETE_GRAY
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        for y in range(height):
            for x in range(width):
                # Base concrete noise
                noise1 = fbm_noise(x / 40, y / 40, octaves=5, seed=seed)
                noise2 = fbm_noise(x / 10, y / 10, octaves=3, seed=seed + 50)
                
                # Aggregate/stones in concrete
                aggregate = voronoi_noise(x / 12, y / 12, seed + 100)[0]
                
                # Cracks
                crack = 0
                if dirty:
                    crack_noise = fbm_noise(x / 80, y / 80, octaves=2, seed=seed + 200)
                    crack = 1 - min(1, crack_noise * 3) if crack_noise < 0.3 else 0
                
                # Combine
                base = palette["base"]
                dark = palette["dark"]
                light = palette["light"]
                
                blend = noise1 * 0.3 + noise2 * 0.2 + aggregate * 0.3
                
                if crack > 0.5:
                    color = [c * 0.6 for c in dark]
                elif blend > 0.6:
                    color = light
                elif blend < 0.4:
                    color = dark
                else:
                    color = base
                
                image.setPixelColor(x, y, QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_plastic_texture(cls, width: int, height: int,
                                 plastic_type: str = "white",
                                 glossy: bool = True,
                                 seed: int = 42) -> QPixmap:
        """
        Generate matte or glossy plastic texture.
        
        Args:
            width, height: Texture dimensions
            plastic_type: "white", "black", "red", "blue", "green", or "orange"
            glossy: Whether to add glossy specular highlights
            seed: Random seed for reproducibility
        """
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"plastic_{plastic_type}_{width}x{height}_{glossy}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = getattr(TextureColors, f"PLASTIC_{plastic_type.upper()}", TextureColors.PLASTIC_WHITE)
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        for y in range(height):
            for x in range(width):
                # Base noise for plastic texture
                noise = fbm_noise(x / 30, y / 30, octaves=3, seed=seed)
                
                # Very fine grain for plastic
                fine_noise = fbm_noise(x / 5, y / 5, octaves=2, seed=seed + 50) * 0.15
                
                # Moulding lines effect (subtle)
                line_effect = math.sin(x * 0.8 + y * 0.2) * 0.5 + 0.5
                line_effect = line_effect * 0.08 if line_effect > 0.85 else 0
                
                base = palette["base"]
                light = palette["light"]
                dark = palette["dark"]
                
                blend = noise * 0.3 + fine_noise + line_effect
                
                if blend > 0.55:
                    color = light
                elif blend < 0.4:
                    color = dark
                else:
                    color = base
                
                # Add subtle surface variation
                variation = (random.random() - 0.5) * 8
                color = [
                    max(0, min(255, color[0] + int(variation))),
                    max(0, min(255, color[1] + int(variation))),
                    max(0, min(255, color[2] + int(variation)))
                ]
                
                # Add glossy highlight if requested
                if glossy:
                    # Simulate light reflection
                    sheen = math.sin(x * 0.15 + y * 0.1) * 0.5 + 0.5
                    sheen = sheen * 0.12 if sheen > 0.7 else 0
                    color = [
                        min(255, color[0] + int(sheen * 40)),
                        min(255, color[1] + int(sheen * 40)),
                        min(255, color[2] + int(sheen * 40))
                    ]
                
                image.setPixelColor(x, y, QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_glass_texture(cls, width: int, height: int,
                              glass_type: str = "clear",
                              frosted: bool = False,
                              seed: int = 42) -> QPixmap:
        """
        Generate glass or frosted glass texture.
        
        Args:
            width, height: Texture dimensions
            glass_type: "clear", "tinted", "amber", or "green"
            frosted: Whether to create frosted glass effect
            seed: Random seed for reproducibility
        """
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"glass_{glass_type}_{width}x{height}_{frosted}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = getattr(TextureColors, f"GLASS_{glass_type.upper()}", TextureColors.GLASS_CLEAR)
        
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        
        for y in range(height):
            for x in range(width):
                base = palette["base"]
                light = palette["light"]
                dark = palette["dark"]
                
                if frosted:
                    # Frosted glass has more diffusion
                    noise1 = fbm_noise(x / 20, y / 20, octaves=4, seed=seed)
                    noise2 = fbm_noise(x / 8, y / 8, octaves=2, seed=seed + 100)
                    
                    # Soft diffuse blend
                    blend = noise1 * 0.5 + noise2 * 0.3
                    
                    if blend > 0.55:
                        color = light
                    elif blend < 0.4:
                        color = dark
                    else:
                        color = base
                    
                    # Add slight opacity variation for frosted look
                    alpha = int(180 + noise1 * 75)
                else:
                    # Clear glass with subtle reflections
                    noise = fbm_noise(x / 40, y / 40, octaves=3, seed=seed)
                    
                    # Reflection lines
                    reflect = math.sin(x * 0.3 + y * 0.1) * 0.5 + 0.5
                    reflect = reflect * 0.15 if reflect > 0.8 else 0
                    
                    # Subtle refraction distortion
                    refract = math.sin(x * 0.2 - y * 0.15) * 0.5 + 0.5
                    refract = refract * 0.1 if refract > 0.85 else 0
                    
                    blend = noise * 0.3 + reflect + refract
                    
                    if blend > 0.5:
                        color = light
                    elif blend < 0.35:
                        color = dark
                    else:
                        color = base
                    
                    # More transparent for clear glass
                    alpha = int(140 + noise * 100)
                
                # Add subtle color variation
                variation = (random.random() - 0.5) * 15
                color = [
                    max(0, min(255, color[0] + int(variation))),
                    max(0, min(255, color[1] + int(variation))),
                    max(0, min(255, color[2] + int(variation)))
                ]
                
                image.setPixelColor(x, y, QColor(*color, alpha))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_carbon_fiber_texture(cls, width: int, height: int,
                                     clear_coat: bool = True,
                                     seed: int = 42) -> QPixmap:
        """
        Generate carbon fiber weave pattern.
        
        Args:
            width, height: Texture dimensions
            clear_coat: Whether to add glossy clear coat layer
            seed: Random seed for reproducibility
        """
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"carbon_{width}x{height}_{clear_coat}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = TextureColors.CARBON_WEAVE
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        for y in range(height):
            for x in range(width):
                # Carbon fiber weave pattern - diagonal交叉
                # Create two diagonal directions
                diag1 = (x + y) % 16
                diag2 = (x - y + 16) % 16
                
                # Weave pattern
                weave1 = 1.0 - abs(diag1 - 8) / 8
                weave2 = 1.0 - abs(diag2 - 8) / 8
                
                # Alternate based on position
                if (x // 8 + y // 8) % 2 == 0:
                    weave = weave1
                else:
                    weave = weave2
                
                # Add fiber direction variation
                fiber_dir = fbm_noise(x / 4, y / 4, octaves=2, seed=seed) * 0.2
                
                # Subtle noise for texture
                noise = fbm_noise(x / 15, y / 15, octaves=3, seed=seed + 50) * 0.15
                
                base = palette["base"]
                light = palette["light"]
                dark = palette["dark"]
                
                blend = weave * 0.5 + fiber_dir + noise
                
                if blend > 0.6:
                    color = light
                elif blend < 0.35:
                    color = dark
                else:
                    color = base
                
                # Add clear coat reflection if requested
                if clear_coat:
                    sheen = math.sin(x * 0.2 + y * 0.15) * 0.5 + 0.5
                    sheen = sheen * 0.15 if sheen > 0.75 else 0
                    color = [
                        min(255, color[0] + int(sheen * 50)),
                        min(255, color[1] + int(sheen * 50)),
                        min(255, color[2] + int(sheen * 50))
                    ]
                
                image.setPixelColor(x, y, QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_fabric_texture(cls, width: int, height: int,
                               fabric_type: str = "canvas",
                               seed: int = 42) -> QPixmap:
        """
        Generate fabric texture with weave pattern.
        
        Args:
            width, height: Texture dimensions
            fabric_type: "canvas", "denim", "tweed", "velvet", or "carbonweave"
            seed: Random seed for reproducibility
        """
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"fabric_{fabric_type}_{width}x{height}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = getattr(TextureColors, f"FABRIC_{fabric_type.upper()}", TextureColors.FABRIC_CANVAS)
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        for y in range(height):
            for x in range(width):
                if fabric_type == "canvas":
                    # Plain weave
                    weave_x = (x % 4) / 4
                    weave_y = (y % 4) / 4
                    weave = abs(weave_x - weave_y)
                    noise = fbm_noise(x / 20, y / 20, octaves=3, seed=seed) * 0.3
                    
                elif fabric_type == "denim":
                    # Diagonal twill weave
                    diag = (x + y * 2) % 8
                    weave = 1.0 - abs(diag - 4) / 4
                    noise = fbm_noise(x / 25, y / 25, octaves=3, seed=seed) * 0.25
                    
                elif fabric_type == "tweed":
                    # Complex herringbone-like pattern
                    herring1 = math.sin(x * 0.5 + y * 0.3) * 0.5 + 0.5
                    herring2 = math.sin(x * 0.3 - y * 0.5) * 0.5 + 0.5
                    weave = (herring1 + herring2) * 0.5
                    noise = fbm_noise(x / 15, y / 15, octaves=4, seed=seed) * 0.35
                    
                elif fabric_type == "velvet":
                    # Velvet has a soft, dense pile
                    pile = fbm_noise(x / 8, y / 8, octaves=2, seed=seed)
                    weave = pile * 0.6 + 0.4
                    noise = fbm_noise(x / 30, y / 30, octaves=3, seed=seed) * 0.2
                    
                elif fabric_type == "carbonweave":
                    # Technical fabric - tight weave
                    diag1 = (x + y) % 6
                    diag2 = (x - y + 6) % 6
                    weave1 = 1.0 - abs(diag1 - 3) / 3
                    weave2 = 1.0 - abs(diag2 - 3) / 3
                    
                    if (x // 6 + y // 6) % 2 == 0:
                        weave = weave1
                    else:
                        weave = weave2
                    noise = fbm_noise(x / 12, y / 12, octaves=2, seed=seed) * 0.15
                else:
                    # Default canvas
                    weave = 0.5
                    noise = fbm_noise(x / 20, y / 20, octaves=3, seed=seed) * 0.3
                
                base = palette["base"]
                light = palette["light"]
                dark = palette["dark"]
                
                blend = weave * 0.5 + noise
                
                if blend > 0.6:
                    color = light
                elif blend < 0.4:
                    color = dark
                else:
                    color = base
                
                # Add thread variation
                thread_var = (random.random() - 0.5) * 12
                color = [
                    max(0, min(255, color[0] + int(thread_var))),
                    max(0, min(255, color[1] + int(thread_var))),
                    max(0, min(255, color[2] + int(thread_var)))
                ]
                
                image.setPixelColor(x, y, QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_gradient_texture(cls, width: int, height: int,
                                  gradient_type: str = "dark",
                                  direction: str = "vertical",
                                  grain: float = 0.05,
                                  seed: int = 42) -> QPixmap:
        """
        Generate gradient background with optional grain/noise.
        
        Args:
            width, height: Texture dimensions
            gradient_type: "dark", "midnight", "sunset", or "forest"
            direction: "vertical", "horizontal", or "diagonal"
            grain: Amount of noise/grain to add (0.0 - 0.2)
            seed: Random seed for reproducibility
        """
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"gradient_{gradient_type}_{width}x{height}_{direction}_{grain}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = getattr(TextureColors, f"GRADIENT_{gradient_type.upper()}", TextureColors.GRADIENT_DARK)
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        light = palette["light"]
        dark = palette["dark"]
        base = palette["base"]
        
        for y in range(height):
            for x in range(width):
                # Calculate gradient position
                if direction == "vertical":
                    t = y / height
                elif direction == "horizontal":
                    t = x / width
                else:  # diagonal
                    t = (x + y) / (width + height)
                
                # Smooth gradient with slight curve
                t = t * t * (3 - 2 * t)  # smoothstep
                
                # Interpolate colors
                color = [
                    int(dark[0] * (1 - t) + light[0] * t),
                    int(dark[1] * (1 - t) + light[1] * t),
                    int(dark[2] * (1 - t) + light[2] * t)
                ]
                
                # Add subtle grain/noise
                if grain > 0:
                    noise = fbm_noise(x / 10, y / 10, octaves=2, seed=seed)
                    noise = (noise - 0.5) * grain * 255
                    color = [
                        max(0, min(255, color[0] + int(noise))),
                        max(0, min(255, color[1] + int(noise))),
                        max(0, min(255, color[2] + int(noise)))
                    ]
                
                image.setPixelColor(x, y, QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_holographic_texture(cls, width: int, height: int,
                                     holo_type: str = "rainbow",
                                     intensity: float = 0.7,
                                     seed: int = 42) -> QPixmap:
        """
        Generate holographic/iridescent surface effect.
        
        Args:
            width, height: Texture dimensions
            holo_type: "rainbow", "silver", or "gold"
            intensity: Effect intensity (0.0 - 1.0)
            seed: Random seed for reproducibility
        """
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"holographic_{holo_type}_{width}x{height}_{intensity}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = getattr(TextureColors, f"HOLOGRAPHIC_{holo_type.upper()}", 
                         TextureColors.HOLOGRAPHIC_RAINBOW)
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        for y in range(height):
            for x in range(width):
                # Calculate position for iridescence
                nx = x / width
                ny = y / height
                
                # Create shifting color bands based on position and viewing angle simulation
                angle = math.atan2(ny - 0.5, nx - 0.5)
                
                # Iridescent color shift - shift hue based on angle and position
                if holo_type == "rainbow":
                    # Full rainbow iridescence
                    hue_shift = (math.sin(angle * 3 + nx * 5 + ny * 3) * 0.5 + 0.5) * intensity
                    
                    # Base color with hue shift
                    base_r, base_g, base_b = palette["base"]
                    
                    # Apply color shift
                    r = int(base_r * (0.7 + hue_shift * 0.5) + math.sin(nx * 10 + ny * 8) * 30 * intensity)
                    g = int(base_g * (0.7 + math.cos(angle * 2) * 0.3 * intensity) + math.sin(ny * 12 + nx * 6) * 25 * intensity)
                    b = int(base_b * (0.8 + hue_shift * 0.4) + math.cos(nx * 8 + ny * 10) * 35 * intensity)
                    
                elif holo_type == "silver":
                    # Silver/monochrome iridescence
                    shimmer = math.sin(angle * 4 + nx * 8 + ny * 6) * 0.5 + 0.5
                    sheen = math.sin(nx * 15 + ny * 12) * 0.5 + 0.5
                    
                    base_val = sum(palette["base"]) / 3
                    val = int(base_val * (0.6 + shimmer * 0.4 * intensity) + sheen * 40 * intensity)
                    r = g = b = val
                    
                else:  # gold
                    # Gold iridescence
                    shift = math.sin(angle * 2.5 + nx * 6 + ny * 4) * 0.5 + 0.5
                    sheen = math.sin(nx * 12 + ny * 10) * 0.5 + 0.5
                    
                    base_r, base_g, base_b = palette["base"]
                    
                    r = int(base_r * (0.7 + shift * 0.3 * intensity) + sheen * 35 * intensity)
                    g = int(base_g * (0.7 + shift * 0.2 * intensity) + sheen * 25 * intensity)
                    b = int(base_b * (0.8 + shift * 0.2 * intensity) + sheen * 10 * intensity)
                
                # Clamp values
                color = [max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))]
                
                image.setPixelColor(x, y, QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_tech_pattern(cls, width: int, height: int,
                              pattern_type: str = "circuit",
                              color_scheme: str = "green",
                              glow: bool = True,
                              seed: int = 42) -> QPixmap:
        """
        Generate tech-inspired grid or circuit board patterns.
        
        Args:
            width, height: Texture dimensions
            pattern_type: "circuit", "grid", or "hex"
            color_scheme: "green", "blue", "cyan", or "dark"
            glow: Whether to add glowing effect
            seed: Random seed for reproducibility
        """
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"tech_{pattern_type}_{color_scheme}_{width}x{height}_{glow}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = getattr(TextureColors, f"TECH_{pattern_type.upper()}_{color_scheme.upper()}", 
                        TextureColors.TECH_CIRCUIT_GREEN)
        if pattern_type == "grid":
            palette = getattr(TextureColors, f"TECH_GRID_{color_scheme.upper()}", 
                           TextureColors.TECH_GRID_DARK)
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        # Fill background
        dark = palette["dark"]
        for y in range(height):
            for x in range(width):
                image.setPixelColor(x, y, QColor(*dark))
        
        # Grid size for patterns
        grid_size = 24
        
        if pattern_type == "circuit":
            # Draw circuit board traces
            for y in range(0, height, grid_size):
                for x in range(0, width, grid_size):
                    # Randomly decide trace direction
                    random.seed(x * 1000 + y + seed)
                    direction = random.randint(0, 3)  # 0=right, 1=down, 2=left, 3=up
                    
                    # Draw trace line
                    trace_len = random.randint(2, 5) * grid_size
                    
                    if direction == 0:  # Horizontal right
                        for dx in range(0, trace_len, grid_size // 4):
                            if 0 <= x + dx < width and 0 <= y < height:
                                color = palette["light"] if glow else palette["base"]
                                # Draw wider trace
                                for w in range(-1, 2):
                                    if 0 <= y + w < height:
                                        image.setPixelColor(x + dx, y + w, QColor(*color))
                    elif direction == 1:  # Vertical down
                        for dy in range(0, trace_len, grid_size // 4):
                            if 0 <= x < width and 0 <= y + dy < height:
                                color = palette["light"] if glow else palette["base"]
                                for w in range(-1, 2):
                                    if 0 <= x + w < width:
                                        image.setPixelColor(x + w, y + dy, QColor(*color))
                    
                    # Add circuit nodes (connection points)
                    if random.random() > 0.5:
                        node_color = palette["light"]
                        for ny in range(-2, 3):
                            for nx in range(-2, 3):
                                if 0 <= x + nx < width and 0 <= y + ny < height:
                                    if nx*nx + ny*ny <= 4:
                                        image.setPixelColor(x + nx, y + ny, QColor(*node_color))
        
        elif pattern_type == "grid":
            # Simple grid pattern
            line_color = palette["light"] if glow else palette["base"]
            
            for y in range(0, height, grid_size):
                for x in range(width):
                    image.setPixelColor(x, y, QColor(*line_color))
            
            for x in range(0, width, grid_size):
                for y in range(height):
                    image.setPixelColor(x, y, QColor(*line_color))
            
            # Add intersection dots
            dot_color = palette["light"]
            for y in range(0, height, grid_size):
                for x in range(0, width, grid_size):
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if 0 <= x + dx < width and 0 <= y + dy < height:
                                if dx*dx + dy*dy <= 1:
                                    image.setPixelColor(x + dx, y + dy, QColor(*dot_color))
        
        elif pattern_type == "hex":
            # Hexagonal grid pattern
            hex_h = grid_size
            hex_w = int(hex_h * 1.732)  # sqrt(3)
            
            for row in range(height // hex_h + 1):
                for col in range(width // hex_w + 2):
                    # Calculate hex center
                    cx = col * hex_w
                    cy = row * hex_h * 0.75
                    
                    if row % 2 == 1:
                        cx += hex_w // 2
                    
                    # Draw hex outline
                    for angle in range(0, 360, 60):
                        rad = math.radians(angle)
                        nx = cx + math.cos(rad) * (hex_h // 2 - 1)
                        ny = cy + math.sin(rad) * (hex_h // 2 - 1)
                        
                        if 0 <= int(nx) < width and 0 <= int(ny) < height:
                            color = palette["light"] if glow else palette["base"]
                            image.setPixelColor(int(nx), int(ny), QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_neumorphic_texture(cls, width: int, height: int,
                                   style: str = "light",
                                   convex: bool = True,
                                   seed: int = 42) -> QPixmap:
        """
        Generate neumorphic soft shadow UI texture.
        
        Args:
            width, height: Texture dimensions
            style: "light", "dark", or "blue"
            convex: True for raised (convex), False for pressed (concave)
            seed: Random seed for reproducibility
        """
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"neumorphic_{style}_{width}x{height}_{convex}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = getattr(TextureColors, f"NEUMORPHIC_{style.upper()}", TextureColors.NEUMORPHIC_LIGHT)
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        base = palette["base"]
        shadow_offset = width // 8
        
        for y in range(height):
            for x in range(width):
                dist_left = x / shadow_offset
                dist_right = (width - x) / shadow_offset
                dist_top = y / shadow_offset
                dist_bottom = (height - y) / shadow_offset
                
                edge_dist = min(dist_left, dist_right, dist_top, dist_bottom)
                shadow = min(1.0, edge_dist)
                
                if convex:
                    highlight = (1 - dist_left) * 0.3 + (1 - dist_top) * 0.3
                    shadow = (1 - dist_right) * 0.25 + (1 - dist_bottom) * 0.25
                else:
                    highlight = (1 - dist_right) * 0.25 + (1 - dist_bottom) * 0.25
                    shadow = (1 - dist_left) * 0.3 + (1 - dist_top) * 0.3
                
                r = int(base[0] + highlight * 30 - shadow * 25)
                g = int(base[1] + highlight * 30 - shadow * 25)
                b = int(base[2] + highlight * 30 - shadow * 25)
                
                color = [max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))]
                
                noise = fbm_noise(x / 15, y / 15, octaves=2, seed=seed) - 0.5
                color = [
                    max(0, min(255, color[0] + int(noise * 8))),
                    max(0, min(255, color[1] + int(noise * 8))),
                    max(0, min(255, color[2] + int(noise * 8)))
                ]
                
                image.setPixelColor(x, y, QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_high_contrast_texture(cls, width: int, height: int,
                                       style: str = "dark",
                                       seed: int = 42) -> QPixmap:
        """Generate high-contrast accessibility-friendly texture."""
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"highcontrast_{style}_{width}x{height}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        palette = getattr(TextureColors, f"HIGH_CONTRAST_{style.upper()}", 
                          TextureColors.HIGH_CONTRAST_DARK)
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        base = palette["base"]
        light = palette["light"]
        
        for y in range(height):
            for x in range(width):
                noise = fbm_noise(x / 50, y / 50, octaves=2, seed=seed) * 0.1
                color = light if noise > 0.4 else base
                image.setPixelColor(x, y, QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_dark_mode_texture(cls, width: int, height: int,
                                  accent_color: str = None,
                                  seed: int = 42) -> QPixmap:
        """Generate dark mode background texture with optional accent."""
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"darkmode_{accent_color}_{width}x{height}_{seed}"
        
        if cache_key in cls._texture_cache:
            return cls._texture_cache[cache_key]
        
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        dark_base = (18, 18, 22)
        dark_light = (35, 35, 45)
        
        accents = {"blue": (60, 100, 180), "purple": (120, 80, 180), 
                   "green": (60, 160, 100), "red": (180, 60, 60), None: None}
        accent = accents.get(accent_color)
        
        for y in range(height):
            for x in range(width):
                gradient = (x / width + y / height) / 2
                noise = fbm_noise(x / 40, y / 40, octaves=2, seed=seed) * 0.15
                
                if gradient + noise > 0.55:
                    color = dark_light
                else:
                    color = dark_base
                
                if accent:
                    accent_noise = fbm_noise(x / 80 + 50, y / 80 + 50, seed + 100)
                    if accent_noise > 0.7:
                        color = [int(color[0] * 0.7 + accent[0] * 0.3),
                                int(color[1] * 0.7 + accent[1] * 0.3),
                                int(color[2] * 0.7 + accent[2] * 0.3)]
                
                image.setPixelColor(x, y, QColor(*color))
        
        pixmap = QPixmap.fromImage(image)
        cls._texture_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_normal_map(cls, texture_pixmap: QPixmap, 
                           strength: float = 1.0) -> QPixmap:
        """
        Generate normal map from texture for bump mapping effect.
        
        Args:
            texture_pixmap: Source texture
            strength: Bump strength (higher = more pronounced)
        """
        # Check for QApplication
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"normal_{id(texture_pixmap)}_{strength}"
        
        if cache_key in cls._normal_map_cache:
            return cls._normal_map_cache[cache_key]
        
        image = texture_pixmap.toImage()
        width = image.width()
        height = image.height()
        
        normal_image = QImage(width, height, QImage.Format.Format_RGB32)
        
        # Convert to grayscale and calculate gradients
        for y in range(height):
            for x in range(width):
                # Get neighboring pixel brightness
                def get_brightness(x, y):
                    if 0 <= x < width and 0 <= y < height:
                        color = image.pixelColor(x, y)
                        return (color.red() + color.green() + color.blue()) / 3 / 255.0
                    return 0.5
                
                # Sample neighboring pixels
                left = get_brightness(x - 1, y)
                right = get_brightness(x + 1, y)
                up = get_brightness(x, y - 1)
                down = get_brightness(x, y + 1)
                
                # Calculate gradients
                dx = (left - right) * strength
                dy = (up - down) * strength
                dz = 1.0
                
                # Normalize
                length = math.sqrt(dx * dx + dy * dy + dz * dz)
                nx = dx / length
                ny = dy / length
                nz = dz / length
                
                # Convert to RGB (map -1..1 to 0..255)
                r = int((nx * 0.5 + 0.5) * 255)
                g = int((ny * 0.5 + 0.5) * 255)
                b = int((nz * 0.5 + 0.5) * 255)
                
                normal_image.setPixelColor(x, y, QColor(r, g, b))
        
        pixmap = QPixmap.fromImage(normal_image)
        cls._normal_map_cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def generate_specular_map(cls, texture_pixmap: QPixmap,
                             intensity: float = 1.0,
                             sharpness: float = 0.5) -> QPixmap:
        """
        Generate specular/gloss map from texture for reflections.
        
        Args:
            texture_pixmap: Source texture
            intensity: Specular intensity (higher = more reflective areas)
            sharpness: Specular sharpness (higher = smaller, sharper highlights)
        """
        if not _ensure_qapplication():
            return QPixmap()
            
        cache_key = f"specular_{id(texture_pixmap)}_{intensity}_{sharpness}"
        
        if cache_key in cls._normal_map_cache:
            return cls._normal_map_cache[cache_key]
        
        image = texture_pixmap.toImage()
        width = image.width()
        height = image.height()
        
        specular_image = QImage(width, height, QImage.Format.Format_RGB32)
        
        # Calculate specular map based on surface smoothness
        for y in range(height):
            for x in range(width):
                color = image.pixelColor(x, y)
                
                # Calculate local contrast (smooth areas = more specular)
                neighbors = []
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            ncolor = image.pixelColor(nx, ny)
                            neighbors.append((ncolor.red() + ncolor.green() + ncolor.blue()) / 3)
                
                if neighbors:
                    avg = sum(neighbors) / len(neighbors)
                    local_contrast = 0
                    for n in neighbors:
                        local_contrast += abs(n - avg)
                    local_contrast /= len(neighbors)
                    
                    # Smooth areas have high specular, rough areas have low
                    specular = max(0, 255 - local_contrast * sharpness * 10)
                    specular = int(specular * intensity)
                else:
                    specular = 128
                
                specular_image.setPixelColor(x, y, QColor(specular, specular, specular))
        
        pixmap = QPixmap.fromImage(specular_image)
        cls._normal_map_cache[cache_key] = pixmap
        return pixmap


# =============================================================================
# TEXTURE STYLES FOR UI ELEMENTS
# =============================================================================

class TextureStyle:
    """Predefined texture styles for UI elements"""
    
    # Standard button textures
    BUTTON_STANDARD = {
        "type": "wood",
        "wood_type": "oak",
        "scale": 12.0,
        "bump_strength": 0.8
    }
    
    BUTTON_RUST = {
        "type": "rust",
        "intensity": 0.8,
        "bump_strength": 1.2
    }
    
    BUTTON_METAL = {
        "type": "metal",
        "metal_type": "steel",
        "scratches": True,
        "bump_strength": 1.0
    }
    
    BUTTON_LEATHER = {
        "type": "leather",
        "leather_type": "brown",
        "worn": True,
        "bump_strength": 0.9
    }
    
    # Panel textures
    PANEL_STANDARD = {
        "type": "metal",
        "metal_type": "steel",
        "scratches": False,
        "bump_strength": 0.6
    }
    
    PANEL_WORN = {
        "type": "concrete",
        "dirty": True,
        "bump_strength": 0.5
    }
    
    PANEL_RUST = {
        "type": "rust",
        "intensity": 0.6,
        "bump_strength": 0.8
    }
    
    PANEL_WOOD = {
        "type": "wood",
        "wood_type": "pine",
        "scale": 10.0,
        "bump_strength": 0.7
    }
    
    # New UI texture styles
    BUTTON_PLASTIC_WHITE = {"type": "plastic", "plastic_type": "white", "glossy": True, "bump_strength": 0.6}
    BUTTON_PLASTIC_BLACK = {"type": "plastic", "plastic_type": "black", "glossy": True, "bump_strength": 0.6}
    BUTTON_PLASTIC_RED = {"type": "plastic", "plastic_type": "red", "glossy": True, "bump_strength": 0.6}
    BUTTON_PLASTIC_BLUE = {"type": "plastic", "plastic_type": "blue", "glossy": True, "bump_strength": 0.6}
    
    PANEL_GLASS_CLEAR = {"type": "glass", "glass_type": "clear", "frosted": False, "bump_strength": 0.3}
    PANEL_GLASS_FROSTED = {"type": "glass", "glass_type": "clear", "frosted": True, "bump_strength": 0.4}
    PANEL_GLASS_TINTED = {"type": "glass", "glass_type": "tinted", "frosted": False, "bump_strength": 0.3}
    
    PANEL_CARBON = {"type": "carbon", "clear_coat": True, "bump_strength": 0.7}
    
    PANEL_FABRIC_CANVAS = {"type": "fabric", "fabric_type": "canvas", "bump_strength": 0.5}
    PANEL_FABRIC_DENIM = {"type": "fabric", "fabric_type": "denim", "bump_strength": 0.5}
    PANEL_FABRIC_VELVET = {"type": "fabric", "fabric_type": "velvet", "bump_strength": 0.4}
    
    BACKGROUND_GRADIENT_DARK = {"type": "gradient", "gradient_type": "dark", "direction": "vertical", "grain": 0.03}
    BACKGROUND_GRADIENT_MIDNIGHT = {"type": "gradient", "gradient_type": "midnight", "direction": "diagonal", "grain": 0.04}
    BACKGROUND_GRADIENT_SUNSET = {"type": "gradient", "gradient_type": "sunset", "direction": "vertical", "grain": 0.05}
    
    BACKGROUND_HOLOGRAPHIC = {"type": "holographic", "holo_type": "rainbow", "intensity": 0.6, "bump_strength": 0.3}
    BACKGROUND_HOLOGRAPHIC_SILVER = {"type": "holographic", "holo_type": "silver", "intensity": 0.5, "bump_strength": 0.3}
    
    BACKGROUND_TECH_CIRCUIT = {"type": "tech", "pattern_type": "circuit", "color_scheme": "green", "glow": True}
    BACKGROUND_TECH_GRID = {"type": "tech", "pattern_type": "grid", "color_scheme": "cyan", "glow": True}
    BACKGROUND_TECH_HEX = {"type": "tech", "pattern_type": "hex", "color_scheme": "blue", "glow": False}
    
    PANEL_NEUMORPHIC_LIGHT = {"type": "neumorphic", "style": "light", "convex": True, "bump_strength": 0.2}
    PANEL_NEUMORPHIC_DARK = {"type": "neumorphic", "style": "dark", "convex": True, "bump_strength": 0.2}
    PANEL_NEUMORPHIC_PRESSED = {"type": "neumorphic", "style": "light", "convex": False, "bump_strength": 0.2}
    
    BACKGROUND_HIGH_CONTRAST = {"type": "highcontrast", "style": "dark", "bump_strength": 0.1}
    BACKGROUND_HIGH_CONTRAST_LIGHT = {"type": "highcontrast", "style": "light", "bump_strength": 0.1}
    BACKGROUND_HIGH_CONTRAST_YELLOW = {"type": "highcontrast", "style": "yellow", "bump_strength": 0.1}
    
    BACKGROUND_DARK_MODE = {"type": "darkmode", "accent_color": None, "bump_strength": 0.1}
    BACKGROUND_DARK_MODE_BLUE = {"type": "darkmode", "accent_color": "blue", "bump_strength": 0.1}
    BACKGROUND_DARK_MODE_PURPLE = {"type": "darkmode", "accent_color": "purple", "bump_strength": 0.1}


# =============================================================================
# RESOLUTION VARIANTS
# =============================================================================

class ResolutionVariant:
    """Resolution variants for different display densities"""
    
    # Standard resolution presets
    SD = 64        # Standard definition (1x)
    HD = 128       # High definition (2x)
    FHD = 256      # Full HD (4x)
    UHD = 512      # Ultra HD (8x)
    
    @classmethod
    def get_all_variants(cls, base_size: int = 64) -> Dict[str, int]:
        """Get all resolution variants based on base size"""
        return {
            "sd": base_size,
            "hd": base_size * 2,
            "fhd": base_size * 4,
            "uhd": base_size * 8
        }
    
    @classmethod
    def get_optimal_size(cls, display_density: float = 1.0) -> int:
        """Get optimal texture size based on display density"""
        if display_density <= 1.0:
            return cls.SD
        elif display_density <= 2.0:
            return cls.HD
        elif display_density <= 3.0:
            return cls.FHD
        else:
            return cls.UHD


# =============================================================================
# TEXTURE PAINTER HELPER
# =============================================================================

class TexturePainter:
    """
    Helper class for painting textures with effects on widgets.
    Supports tiling, scaling, lighting effects, and bump mapping.
    """
    
    @staticmethod
    def paint_texture(painter: QPainter, rect: QRect, 
                      texture: QPixmap, 
                      tiled: bool = True,
                      scaled: bool = True):
        """
        Paint a texture onto a rectangle.
        
        Args:
            painter: QPainter to draw with
            rect: Target rectangle
            texture: Texture pixmap to draw
            tiled: Whether to tile the texture
            scaled: Whether to scale to fit rect
        """
        if texture.isNull():
            return
        
        if tiled:
            # Tile the texture
            painter.save()
            painter.translate(rect.x(), rect.y())
            
            # Calculate tiling
            tile_width = texture.width()
            tile_height = texture.height()
            
            if scaled:
                tile_width = rect.width() // 4  # Scale down tiles for better look
                tile_height = rect.height() // 4
            
            scaled_texture = texture.scaled(
                max(1, tile_width), 
                max(1, tile_height),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Draw tiled
            pattern = QBrush(scaled_texture)
            pattern.setTexture(scaled_texture)
            painter.fillRect(rect, pattern)
            
            painter.restore()
        else:
            # Draw stretched
            if scaled:
                scaled = texture.scaled(rect.size(), 
                                        Qt.AspectRatioMode.IgnoreAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap(rect.x() + (rect.width() - scaled.width()) // 2,
                                   rect.y() + (rect.height() - scaled.height()) // 2,
                                   scaled)
            else:
                painter.drawPixmap(rect, texture)
    
    @staticmethod
    def paint_bumpmapped(painter: QPainter, rect: QRect,
                         texture: QPixmap,
                         normal_map: QPixmap,
                         light_pos: Tuple[int, int] = None):
        """
        Paint texture with bump mapping effect.
        
        Args:
            painter: QPainter to draw with
            rect: Target rectangle
            texture: Diffuse texture
            normal_map: Normal map for bump effect
            light_pos: Light source position (x, y) relative to widget
        """
        # First draw base texture
        TexturePainter.paint_texture(painter, rect, texture, tiled=True)
        
        if normal_map.isNull() or texture.isNull():
            return
        
        # Apply lighting effect based on normal map
        painter.save()
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SoftLight)
        
        # Simple lighting simulation
        if light_pos is None:
            light_pos = (rect.width() // 2, rect.height() // 4)
        
        light_x, light_y = light_pos
        
        # Draw highlight based on simulated light
        gradient = QRadialGradient(light_x, light_y, rect.width() // 2)
        gradient.setColorAt(0, QColor(255, 255, 255, 60))
        gradient.setColorAt(0.5, QColor(255, 255, 255, 20))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        
        painter.fillRect(rect, gradient)
        
        # Add subtle specular highlight
        highlight = QLinearGradient(
            light_x - rect.x(), light_y - rect.y(),
            light_x - rect.x() + 50, light_y - rect.y() + 50
        )
        highlight.setColorAt(0, QColor(255, 255, 255, 40))
        highlight.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.fillRect(rect, highlight)
        
        painter.restore()
    
    @staticmethod
    def paint_worn_edge(painter: QPainter, rect: QRect, 
                        border_color: QColor,
                        intensity: float = 0.3):
        """
        Paint worn edge effect on borders.
        
        Args:
            painter: QPainter to draw with
            rect: Target rectangle
            border_color: Base border color
            intensity: Wear intensity (0-1)
        """
        from PyQt6.QtGui import QPen
        
        # Create worn border effect
        border_rect = rect.adjusted(0, 0, 0, 0)
        
        # Draw main border
        pen = QPen(border_color)
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Add some irregularity to the border
        painter.drawRect(border_rect)
        
        # Add highlight on one side for 3D effect
        highlight_color = QColor(
            min(255, border_color.red() + 40),
            min(255, border_color.green() + 40),
            min(255, border_color.blue() + 40),
            int(100 * intensity)
        )
        
        pen = QPen(highlight_color)
        pen.setWidth(1)
        painter.setPen(pen)
        
        # Top and left highlight
        painter.drawLine(rect.topLeft().x() + 2, rect.top() + 2,
                         rect.topRight().x() - 2, rect.top() + 2)
        painter.drawLine(rect.left() + 2, rect.top() + 2,
                         rect.left() + 2, rect.bottom() - 2)
        
        # Add shadow on bottom and right
        shadow_color = QColor(
            max(0, border_color.red() - 40),
            max(0, border_color.green() - 40),
            max(0, border_color.blue() - 40),
            int(100 * intensity)
        )
        
        pen = QPen(shadow_color)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(rect.left() + 2, rect.bottom() - 2,
                         rect.right() - 2, rect.bottom() - 2)
        painter.drawLine(rect.right() - 2, rect.top() + 2,
                         rect.right() - 2, rect.bottom() - 2)
    
    @staticmethod
    def make_seamless(texture: QPixmap) -> QPixmap:
        """
        Make a texture seamless for tiling by blending edges.
        
        Args:
            texture: Source texture to make seamless
            
        Returns:
            Seamless version of the texture
        """
        if texture.isNull():
            return texture
            
        image = texture.toImage()
        width = image.width()
        height = image.height()
        
        # Create new image for seamless version
        seamless = QImage(width, height, QImage.Format.Format_RGB32)
        
        # Blend width for edge smoothing
        blend_width = width // 8
        blend_height = height // 8
        
        for y in range(height):
            for x in range(width):
                # Calculate blending weights for edges
                # Horizontal wrapping
                x_wrap = x
                x_opposite = (x + width // 2) % width
                
                # Vertical wrapping
                y_wrap = y
                y_opposite = (y + height // 2) % height
                
                # Calculate horizontal blend factor
                h_blend = 1.0
                if x < blend_width:
                    h_blend = x / blend_width
                elif x > width - blend_width:
                    h_blend = (width - x) / blend_width
                
                # Calculate vertical blend factor
                v_blend = 1.0
                if y < blend_height:
                    v_blend = y / blend_height
                elif y > height - blend_height:
                    v_blend = (height - y) / blend_height
                
                # Combine blend factors
                blend = min(h_blend, v_blend)
                
                # Get colors from current and wrapped positions
                color_current = image.pixelColor(x, y)
                color_wrapped_h = image.pixelColor(x_opposite, y)
                color_wrapped_v = image.pixelColor(x, y_opposite)
                color_wrapped_both = image.pixelColor(x_opposite, y_opposite)
                
                # Blend colors
                r = int(color_current.red() * blend + 
                       color_wrapped_h.red() * (1 - blend) * 0.3 +
                       color_wrapped_v.red() * (1 - blend) * 0.3 +
                       color_wrapped_both.red() * (1 - blend) * 0.4)
                g = int(color_current.green() * blend + 
                       color_wrapped_h.green() * (1 - blend) * 0.3 +
                       color_wrapped_v.green() * (1 - blend) * 0.3 +
                       color_wrapped_both.green() * (1 - blend) * 0.4)
                b = int(color_current.blue() * blend + 
                       color_wrapped_h.blue() * (1 - blend) * 0.3 +
                       color_wrapped_v.blue() * (1 - blend) * 0.3 +
                       color_wrapped_both.blue() * (1 - blend) * 0.4)
                
                seamless.setPixelColor(x, y, QColor(
                    max(0, min(255, r)),
                    max(0, min(255, g)),
                    max(0, min(255, b))
                ))
        
        return QPixmap.fromImage(seamless)
    
    @staticmethod
    def paint_seamless(painter: QPainter, rect: QRect,
                      texture: QPixmap,
                      tile_size: int = 64):
        """
        Paint texture with seamless tiling.
        
        Args:
            painter: QPainter to draw with
            rect: Target rectangle
            texture: Texture to tile (should be seamless)
            tile_size: Size of each tile
        """
        if texture.isNull():
            return
            
        # Scale texture to tile size
        scaled = texture.scaled(
            tile_size, tile_size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Create pattern brush
        pattern = QBrush(scaled)
        pattern.setTexture(scaled)
        
        painter.fillRect(rect, pattern)
    
    @staticmethod
    def paint_with_parallax(painter: QPainter, rect: QRect,
                           texture: QPixmap,
                           offset: Tuple[float, float] = (0, 0)):
        """
        Paint texture with parallax scrolling effect.
        
        Args:
            painter: QPainter to draw with
            rect: Target rectangle
            texture: Texture to draw
            offset: (x, y) offset for parallax effect
        """
        if texture.isNull():
            return
            
        painter.save()
        
        # Apply parallax offset
        offset_x = int(offset[0] * rect.width()) % texture.width()
        offset_y = int(offset[1] * rect.height()) % texture.height()
        
        # Draw texture with offset (wrapping)
        for y in range(-1, (rect.height() // texture.height()) + 2):
            for x in range(-1, (rect.width() // texture.width()) + 2):
                dest_x = x * texture.width() + offset_x - texture.width()
                dest_y = y * texture.height() + offset_y - texture.height()
                
                painter.drawPixmap(
                    rect.x() + dest_x,
                    rect.y() + dest_y,
                    texture
                )
        
        painter.restore()


# =============================================================================
# TEXTURE CACHE MANAGER
# =============================================================================

class TextureCache:
    """
    Manages texture caching and preloading.
    """
    
    # Pre-generated common textures
    _preloaded: Dict[str, QPixmap] = {}
    
    @classmethod
    def preload_common_textures(cls):
        """Preload commonly used textures for faster startup"""
        common_textures = [
            ("btn_standard", 64, 64, TextureStyle.BUTTON_STANDARD),
            ("btn_rust", 64, 64, TextureStyle.BUTTON_RUST),
            ("btn_metal", 64, 64, TextureStyle.BUTTON_METAL),
            ("btn_leather", 64, 64, TextureStyle.BUTTON_LEATHER),
            ("panel_standard", 128, 128, TextureStyle.PANEL_STANDARD),
            ("panel_rust", 128, 128, TextureStyle.PANEL_RUST),
            ("panel_wood", 128, 128, TextureStyle.PANEL_WOOD),
        ]
        
        for name, w, h, style in common_textures:
            texture = cls._generate_from_style(w, h, style)
            cls._preloaded[name] = texture
    
    @classmethod
    def _generate_from_style(cls, width: int, height: int, 
                             style: dict) -> QPixmap:
        """Generate texture from style dict"""
        tex_type = style.get("type", "metal")
        
        if tex_type == "wood":
            return TextureGenerator.generate_wood_texture(
                width, height,
                wood_type=style.get("wood_type", "oak"),
                scale=style.get("scale", 8.0),
                seed=style.get("seed", 42)
            )
        elif tex_type == "metal":
            return TextureGenerator.generate_metal_texture(
                width, height,
                metal_type=style.get("metal_type", "steel"),
                scratches=style.get("scratches", True),
                seed=style.get("seed", 42)
            )
        elif tex_type == "rust":
            return TextureGenerator.generate_rust_texture(
                width, height,
                intensity=style.get("intensity", 0.7),
                seed=style.get("seed", 42)
            )
        elif tex_type == "leather":
            return TextureGenerator.generate_leather_texture(
                width, height,
                leather_type=style.get("leather_type", "brown"),
                worn=style.get("worn", True),
                seed=style.get("seed", 42)
            )
        elif tex_type == "concrete":
            return TextureGenerator.generate_concrete_texture(
                width, height,
                dirty=style.get("dirty", True),
                seed=style.get("seed", 42)
            )
        elif tex_type == "plastic":
            return TextureGenerator.generate_plastic_texture(
                width, height,
                plastic_type=style.get("plastic_type", "white"),
                glossy=style.get("glossy", True),
                seed=style.get("seed", 42)
            )
        elif tex_type == "glass":
            return TextureGenerator.generate_glass_texture(
                width, height,
                glass_type=style.get("glass_type", "clear"),
                frosted=style.get("frosted", False),
                seed=style.get("seed", 42)
            )
        elif tex_type == "carbon":
            return TextureGenerator.generate_carbon_fiber_texture(
                width, height,
                clear_coat=style.get("clear_coat", True),
                seed=style.get("seed", 42)
            )
        elif tex_type == "fabric":
            return TextureGenerator.generate_fabric_texture(
                width, height,
                fabric_type=style.get("fabric_type", "canvas"),
                seed=style.get("seed", 42)
            )
        elif tex_type == "gradient":
            return TextureGenerator.generate_gradient_texture(
                width, height,
                gradient_type=style.get("gradient_type", "dark"),
                direction=style.get("direction", "vertical"),
                grain=style.get("grain", 0.05),
                seed=style.get("seed", 42)
            )
        elif tex_type == "holographic":
            return TextureGenerator.generate_holographic_texture(
                width, height,
                holo_type=style.get("holo_type", "rainbow"),
                intensity=style.get("intensity", 0.7),
                seed=style.get("seed", 42)
            )
        elif tex_type == "tech":
            return TextureGenerator.generate_tech_pattern(
                width, height,
                pattern_type=style.get("pattern_type", "circuit"),
                color_scheme=style.get("color_scheme", "green"),
                glow=style.get("glow", True),
                seed=style.get("seed", 42)
            )
        elif tex_type == "neumorphic":
            return TextureGenerator.generate_neumorphic_texture(
                width, height,
                style=style.get("style", "light"),
                convex=style.get("convex", True),
                seed=style.get("seed", 42)
            )
        elif tex_type == "highcontrast":
            return TextureGenerator.generate_high_contrast_texture(
                width, height,
                style=style.get("style", "dark"),
                seed=style.get("seed", 42)
            )
        elif tex_type == "darkmode":
            return TextureGenerator.generate_dark_mode_texture(
                width, height,
                accent_color=style.get("accent_color"),
                seed=style.get("seed", 42)
            )
        
        # Default fallback
        return TextureGenerator.generate_metal_texture(width, height)
    
    @classmethod
    def get_texture(cls, name: str) -> Optional[QPixmap]:
        """Get preloaded texture by name"""
        return cls._preloaded.get(name)
    
    @classmethod
    def clear(cls):
        """Clear all cached textures"""
        TextureGenerator.clear_cache()
        cls._preloaded.clear()


# =============================================================================
# QAPPLICATION CHECK HELPER
# =============================================================================

def _ensure_qapplication() -> bool:
    """
    Ensure a QApplication instance exists.
    Returns True if QApplication is available, False otherwise.
    This prevents crashes when trying to create QImage/QPixmap without QApplication.
    """
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            return True
        # Try QCoreApplication as fallback
        from PyQt6.QtCore import QCoreApplication
        app = QCoreApplication.instance()
        if app is not None:
            return True
        # No application instance found
        import logging
        logging.getLogger(__name__).debug("No QApplication instance found for texture generation")
        return False
    except (ImportError, RuntimeError) as e:
        import logging
        logging.getLogger(__name__).debug(f"Error checking QApplication: {e}")
        return False
    except Exception as e:
        import logging
        logging.getLogger(__name__).debug(f"Unexpected error checking QApplication: {e}")
        return False


# Preload on module import - but only if QApplication exists
# This prevents crashes when importing before QApplication is created
def _try_preload():
    """Try to preload textures, safely handle case where QApplication doesn't exist yet"""
    if not _ensure_qapplication():
        return  # Skip preloading if no QApplication
    
    try:
        TextureCache.preload_common_textures()
    except Exception:
        pass  # Ignore preload errors

_try_preload()
