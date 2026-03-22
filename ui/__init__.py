# UI module for Fallout Dialogue Creator

# Theme modules
from ui.fallout_theme import FalloutColors, FalloutFonts, FalloutUIHelpers

# Skeuomorphic theme system
from ui.skeuomorphic_theme import (
    SkeuomorphicTheme,
    MahoganyBrassTheme,
    BrushedSteelBlueTheme,
    IvoryLeatherGoldTheme,
    CarbonFiberOrangeTheme,
    VintageCreamCopperTheme,
    SkeuomorphicThemeManager,
    get_theme_manager,
    set_skeuomorphic_theme,
    apply_skeuomorphic_theme,
    get_current_skeuomorphic_theme
)

# Skeuomorphic widgets
from ui.skeuomorphic_widgets import (
    SkeuomorphicWidget,
    SkeuomorphicButton,
    SkeuomorphicSlider,
    SkeuomorphicProgressBar,
    SkeuomorphicToggle,
    SkeuomorphicScrollBar,
    SkeuomorphicPanel,
    ThemeSelectorWidget,
    apply_skeuomorphic_theme as apply_skeuomorphic_widget_theme,
    get_skeuomorphic_stylesheet
)

# Skeuomorphic window
from ui.skeuomorphic_window import (
    SkeuomorphicTitleBar,
    SkeuomorphicWindow,
    WindowButton,
    create_skeuomorphic_window
)

# Demo
from ui.skeuomorphic_demo import (
    SkeuomorphicDemoWidget,
    SkeuomorphicDemoWindow,
    ThemePreviewWidget,
    run_demo
)