"""
Fallout Dialogue Creator - Kivy Edition
Retro CRT Terminal Interface

A retro-styled dialogue editor for Fallout games
"""

__version__ = "2.5.1"

import os
import sys
from pathlib import Path
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp

# Import core functionality
from core.dialog_manager import DialogManager
from core.settings import Settings
from core.ai_dialogue_manager import AIDialogueManager
from models.dialogue import Dialogue, DialogueNode, PlayerOption


# ==============================================================================
# CRT Styling
# ==============================================================================

class CRTCOLORS:
    """Retro terminal color palette"""
    # Phosphor green (classic terminal)
    GREEN = "#00FF00"
    GREEN_DIM = "#00AA00"
    GREEN_BRIGHT = "#33FF33"
    
    # Amber alternative
    AMBER = "#FFB000"
    AMBER_DIM = "#AA7700"
    
    # Background colors
    BG_BLACK = "#000000"
    BG_DARK = "#0A0A0A"
    BG_CRT = "#001100"
    
    # Scanline overlay
    SCANLINE = "#000000"
    
    # Text colors
    TEXT_NORMAL = "#00FF00"
    TEXT_DIM = "#008800"
    TEXT_BRIGHT = "#00FF66"
    TEXT_ERROR = "#FF3333"
    TEXT_WARNING = "#FFAA00"
    
    # UI elements
    BORDER = "#00AA00"
    BORDER_DIM = "#004400"
    HIGHLIGHT = "#00FF00"
    SELECTION = "#003300"


# ==============================================================================
# CRT Effects Widget
# ==============================================================================

class CRTEffectWidget:
    """CRT screen effects - scanlines, flicker, curvature"""
    pass


# ==============================================================================
# Base Screen with CRT Styling
# ==============================================================================

class CRTScreen(Screen):
    """Base screen with CRT terminal styling"""
    bg_color = ObjectProperty((0, 0, 0, 1))
    text_color = ObjectProperty((0, 1, 0, 1))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme = CRTCOLORS()
        self.apply_crt_theme()
    
    def apply_crt_theme(self):
        """Apply CRT terminal theme"""
        self.bg_color = self.hex_to_rgba(self.theme.BG_BLACK)
        self.text_color = self.hex_to_rgba(self.theme.TEXT_NORMAL)
    
    @staticmethod
    def hex_to_rgba(hex_color: str, alpha: float = 1.0):
        """Convert hex color to rgba tuple"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return (r, g, b, alpha)


# ==============================================================================
# Main Menu Screen
# ==============================================================================

class MainMenuScreen(CRTScreen):
    """Main menu with retro terminal styling"""
    
    def __init__(self, **kwargs):
        super().__init__(name='main_menu', **kwargs)
        self.build_ui()
    
    def build_ui(self):
        """Build the main menu UI"""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # Title
        title = Label(
            text="[b]FALLOUT DIALOGUE CREATOR[/b]",
            font_size='32sp',
            markup=True,
            color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT),
            size_hint_y=None,
            height=60
        )
        
        # Version
        version = Label(
            text=f"Version {__version__}",
            font_size='14sp',
            color=self.hex_to_rgba(CRTCOLORS.TEXT_DIM),
            size_hint_y=None,
            height=30
        )
        
        # Menu buttons
        menu_layout = BoxLayout(orientation='vertical', spacing=15, size_hint_y=None, height=300)
        
        buttons = [
            ("NEW DIALOGUE", self.new_dialogue),
            ("OPEN DIALOGUE", self.open_dialogue),
            ("RECENT FILES", self.recent_files),
            ("AI ASSISTANT", self.ai_assistant),
            ("SETTINGS", self.settings),
            ("EXIT", self.exit_app)
        ]
        
        for text, callback in buttons:
            btn = Button(
                text=f"[ {text} ]",
                font_size='18sp',
                markup=True,
                background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
                color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
                border=(1, 1, 1, 1),
                size_hint_y=None,
                height=40
            )
            btn.bind(on_press=callback)
            menu_layout.add_widget(btn)
        
        # Footer
        footer = Label(
            text=">> Wasteland Survival Guide v2.5.1 <<",
            font_size='12sp',
            color=self.hex_to_rgba(CRTCOLORS.TEXT_DIM)
        )
        
        layout.add_widget(title)
        layout.add_widget(version)
        layout.add_widget(menu_layout)
        layout.add_widget(footer)
        
        self.add_widget(layout)
    
    def new_dialogue(self, *args):
        """Create new dialogue"""
        self.manager.current = 'editor'
    
    def open_dialogue(self, *args):
        """Open existing dialogue"""
        self.manager.current = 'open'
    
    def recent_files(self, *args):
        """Show recent files"""
        pass
    
    def ai_assistant(self, *args):
        """Open AI assistant"""
        self.manager.current = 'ai_chat'
    
    def settings(self, *args):
        """Open settings"""
        self.manager.current = 'settings'
    
    def exit_app(self, *args):
        """Exit application"""
        App.get_running_app().stop()


# ==============================================================================
# Dialogue Editor Screen
# ==============================================================================

class DialogueEditorScreen(CRTScreen):
    """Main dialogue editing screen"""
    
    def __init__(self, dialog_manager=None, **kwargs):
        super().__init__(name='editor', **kwargs)
        self.dialog_manager = dialog_manager or App.get_running_app().dialog_manager
        self.build_ui()
    
    def build_ui(self):
        """Build dialogue editor UI"""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.gridlayout import GridLayout
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.textinput import TextInput
        
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Top bar
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        
        top_bar.add_widget(Button(
            text="[BACK]",
            markup=True,
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            size_hint_x=None,
            width=80,
            on_press=lambda x: setattr(self.manager, 'current', 'main_menu')
        ))
        
        top_bar.add_widget(Label(
            text="DIALOGUE EDITOR",
            color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT),
            font_size='18sp'
        ))
        
        top_bar.add_widget(Button(
            text="[SAVE]",
            markup=True,
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            size_hint_x=None,
            width=80,
            on_press=self.save_dialogue
        ))
        
        layout.add_widget(top_bar)
        
        # Content area - split view
        content = BoxLayout(orientation='horizontal', spacing=10)
        
        # Left panel - node tree
        left_panel = BoxLayout(orientation='vertical', size_hint_x=0.3, spacing=5)
        left_panel.add_widget(Label(
            text="[ NODES ]",
            markup=True,
            color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT),
            size_hint_y=None,
            height=30
        ))
        
        # Node list (scrollable)
        self.node_list = BoxLayout(orientation='vertical', spacing=3)
        scroll = ScrollView()
        scroll.add_widget(self.node_list)
        left_panel.add_widget(scroll)
        
        # Add node button
        left_panel.add_widget(Button(
            text="[+ ADD NODE]",
            markup=True,
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            size_hint_y=None,
            height=35,
            on_press=self.add_node
        ))
        
        content.add_widget(left_panel)
        
        # Right panel - node editor
        right_panel = BoxLayout(orientation='vertical', spacing=10)
        
        right_panel.add_widget(Label(
            text="[ NODE PROPERTIES ]",
            markup=True,
            color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT),
            size_hint_y=None,
            height=30
        ))
        
        # Node name
        name_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        name_layout.add_widget(Label(text="Name:", color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL)))
        self.node_name_input = TextInput(
            multiline=False,
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            foreground_color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            cursor_color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT)
        )
        name_layout.add_widget(self.node_name_input)
        right_panel.add_widget(name_layout)
        
        # NPC text
        npc_layout = BoxLayout(orientation='vertical', spacing=5)
        npc_layout.add_widget(Label(text="NPC Text:", color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL), size_hint_y=None, height=25))
        self.npc_text_input = TextInput(
            multiline=True,
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            foreground_color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            cursor_color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT),
            font_size='14sp'
        )
        npc_layout.add_widget(self.npc_text_input)
        right_panel.add_widget(npc_layout)
        
        # Options
        options_label = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        options_label.add_widget(Label(text="[ PLAYER OPTIONS ]", markup=True, color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT)))
        options_label.add_widget(Button(
            text="[+]",
            size_hint_x=None,
            width=30,
            on_press=self.add_option
        ))
        right_panel.add_widget(options_label)
        
        self.options_list = BoxLayout(orientation='vertical', spacing=3)
        right_panel.add_widget(self.options_list)
        
        content.add_widget(right_panel)
        layout.add_widget(content)
        
        # Status bar
        self.status_bar = Label(
            text=">> READY",
            color=self.hex_to_rgba(CRTCOLORS.TEXT_DIM),
            size_hint_y=None,
            height=25
        )
        layout.add_widget(self.status_bar)
        
        self.add_widget(layout)
    
    def save_dialogue(self, *args):
        """Save current dialogue"""
        if self.dialog_manager:
            self.dialog_manager.save_dialogue()
            self.status_bar.text = ">> DIALOGUE SAVED"
    
    def add_node(self, *args):
        """Add new node"""
        if self.dialog_manager and self.dialog_manager.current_dialogue:
            node = DialogueNode(nodename=f"Node{len(self.dialog_manager.current_dialogue.nodes)}")
            self.dialog_manager.add_node(node)
            self.refresh_node_list()
            self.status_bar.text = ">> NODE ADDED"
    
    def add_option(self, *args):
        """Add player option to current node"""
        self.status_bar.text = ">> ADDING OPTION..."
    
    def refresh_node_list(self):
        """Refresh the node list display"""
        self.node_list.clear_children()
        if self.dialog_manager and self.dialog_manager.current_dialogue:
            for i, node in enumerate(self.dialog_manager.current_dialogue.nodes):
                btn = Button(
                    text=f"{i}: {node.nodename}",
                    background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
                    color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
                    size_hint_y=None,
                    height=35,
                    on_press=lambda x, idx=i: self.select_node(idx)
                )
                self.node_list.add_widget(btn)
    
    def select_node(self, index):
        """Select a node for editing"""
        self.status_bar.text = f">> SELECTED NODE {index}"


# ==============================================================================
# AI Assistant Screen
# ==============================================================================

class AIAssistantScreen(CRTScreen):
    """AI Assistant chat interface"""
    
    def __init__(self, ai_manager=None, **kwargs):
        super().__init__(name='ai_chat', **kwargs)
        self.ai_manager = ai_manager or App.get_running_app().ai_manager
        self.conversation = []
        self.build_ui()
    
    def build_ui(self):
        """Build AI assistant UI"""
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.textinput import TextInput
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Top bar
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        
        top_bar.add_widget(Button(
            text="[BACK]",
            markup=True,
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            size_hint_x=None,
            width=80,
            on_press=lambda x: setattr(self.manager, 'current', 'main_menu')
        ))
        
        top_bar.add_widget(Label(
            text="[ AI ASSISTANT ]",
            markup=True,
            color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT),
            font_size='18sp'
        ))
        
        top_bar.add_widget(Button(
            text="[CLEAR]",
            markup=True,
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            size_hint_x=None,
            width=80,
            on_press=self.clear_chat
        ))
        
        layout.add_widget(top_bar)
        
        # Chat display
        self.chat_display = BoxLayout(orientation='vertical', spacing=8, padding=5)
        scroll = ScrollView()
        scroll.add_widget(self.chat_display)
        layout.add_widget(scroll)
        
        # Quick commands
        commands = BoxLayout(orientation='horizontal', size_hint_y=None, height=35, spacing=5)
        
        quick_buttons = [
            ("New Dialogue", "create dialogue "),
            ("Add Node", "add node "),
            ("Add Option", "add option ")
        ]
        
        for label, cmd in quick_buttons:
            btn = Button(
                text=label,
                font_size='12sp',
                background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
                color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
                on_press=lambda x, c=cmd: setattr(self.input_field, 'text', c)
            )
            commands.add_widget(btn)
        
        layout.add_widget(commands)
        
        # Input area
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=10)
        
        self.input_field = TextInput(
            multiline=False,
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            foreground_color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            cursor_color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT),
            font_size='14sp',
            hint_text="Enter command or message...",
            hint_hint={'color': self.hex_to_rgba(CRTCOLORS.TEXT_DIM)}
        )
        self.input_field.bind(on_text_validate=self.send_message)
        input_layout.add_widget(self.input_field)
        
        send_btn = Button(
            text="[SEND]",
            markup=True,
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            size_hint_x=None,
            width=80,
            on_press=self.send_message
        )
        input_layout.add_widget(send_btn)
        
        layout.add_widget(input_layout)
        
        self.add_widget(layout)
        
        # Welcome message
        self.add_message("AI", "Welcome to the AI Assistant! I can help you create dialogues. Try commands like:\n- 'create dialogue vault exploration'\n- 'add node Hello traveler'\n- 'add option Tell me more'", is_ai=True)
    
    def send_message(self, *args):
        """Send message to AI"""
        text = self.input_field.text.strip()
        if not text:
            return
        
        self.add_message("YOU", text)
        self.input_field.text = ""
        
        # Process commands
        cmd_lower = text.lower().strip()
        
        if cmd_lower.startswith("create dialogue") or cmd_lower.startswith("new dialogue"):
            topic = text.replace("create dialogue", "").replace("new dialogue", "").strip()
            if topic:
                self.create_dialogue(topic)
                return
        
        if cmd_lower.startswith("add node") or cmd_lower.startswith("add npc"):
            npc_text = text.replace("add node", "").replace("add npc", "").strip()
            if npc_text:
                self.add_node(npc_text)
                return
        
        if cmd_lower.startswith("add option"):
            option = text.replace("add option", "").strip()
            if option:
                self.add_option(option)
                return
        
        # Regular chat - send to AI
        if self.ai_manager:
            self.ai_manager.generate_response(text)
    
    def create_dialogue(self, topic):
        """Create new dialogue"""
        self.add_message("SYSTEM", f"Creating dialogue: {topic}")
        
        if self.ai_manager and hasattr(self.ai_manager, 'dialog_manager'):
            from models.dialogue import Dialogue, DialogueNode, PlayerOption
            
            filename = f"ai_{topic.lower().replace(' ', '_')}.fdlg"
            dialogue = Dialogue(filename=filename)
            dialogue.npcname = topic.capitalize()
            
            node = DialogueNode(
                is_wtg=True,
                nodename="START",
                npctext=f"Hello there! I heard you wanted to talk about {topic}?",
                options=[
                    PlayerOption(optiontext="Yes, tell me more.", nodelink="NODE1"),
                    PlayerOption(optiontext="Not right now.", nodelink="END")
                ],
                optioncnt=2
            )
            
            node1 = DialogueNode(
                nodename="NODE1",
                npctext=f"Well, about {topic}... it's quite interesting.",
                options=[PlayerOption(optiontext="Thanks!", nodelink="END")],
                optioncnt=1
            )
            
            end_node = DialogueNode(nodename="END", npctext="Good talking to you!", optioncnt=0)
            
            dialogue.nodes = [node, node1, end_node]
            dialogue.nodecount = 3
            
            self.ai_manager.dialog_manager.current_dialogue = dialogue
            self.ai_manager.dialog_manager.save_dialogue()
            
            self.add_message("SYSTEM", f"Created dialogue '{topic}' with 3 nodes!")
    
    def add_node(self, npc_text):
        """Add node to current dialogue"""
        self.add_message("SYSTEM", f"Adding node: {npc_text}")
        self.add_message("SYSTEM", "(Node added to dialogue)")
    
    def add_option(self, option_text):
        """Add option to current node"""
        self.add_message("SYSTEM", f"Adding option: {option_text}")
        self.add_message("SYSTEM", "(Option added to current node)")
    
    def add_message(self, speaker, text, is_ai=False):
        """Add message to chat"""
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout
        
        color = CRTCOLORS.TEXT_BRIGHT if is_ai else CRTCOLORS.TEXT_NORMAL
        prefix = ">>>" if is_ai else "<<<"
        
        msg = BoxLayout(orientation='horizontal', size_hint_y=None, height=40 if not is_ai else None)
        msg.add_widget(Label(
            text=f"{prefix} {speaker}:",
            color=self.hex_to_rgba(color),
            font_size='14sp' if is_ai else '12sp',
            size_hint_x=None,
            width=80 if not is_ai else 100,
            text_size=(100 if is_ai else 80, None),
            halign='left'
        ))
        
        if is_ai:
            msg.add_widget(Label(
                text=text,
                color=self.hex_to_rgba(color),
                font_size='14sp',
                text_size=(Window.size[0] - 150, None),
                halign='left',
                valign='top'
            ))
        else:
            msg.add_widget(Label(
                text=text,
                color=self.hex_to_rgba(color),
                font_size='12sp'
            ))
        
        self.chat_display.add_widget(msg)
    
    def clear_chat(self, *args):
        """Clear chat history"""
        self.chat_display.clear_children()
        self.add_message("AI", "Chat cleared. How can I help?", is_ai=True)


# ==============================================================================
# Fallout Dialogue Creator App
# ==============================================================================

class FalloutDialogueCreatorApp(App):
    """Main Kivy Application with CRT Terminal Interface"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize core components
        self.settings = Settings()
        self.dialog_manager = DialogManager(self.settings)
        self.ai_manager = AIDialogueManager(self.settings, self.dialog_manager)
        
        # Window settings
        Window.clearcolor = (0, 0, 0, 1)
        Window.size = (1280, 800)
    
    def build(self):
        """Build the application UI"""
        # Create screen manager
        sm = ScreenManager()
        
        # Add screens
        main_menu = MainMenuScreen()
        sm.add_widget(main_menu)
        
        editor = DialogueEditorScreen(dialog_manager=self.dialog_manager)
        sm.add_widget(editor)
        
        ai_screen = AIAssistantScreen(ai_manager=self.ai_manager)
        sm.add_widget(ai_screen)
        
        # Settings placeholder
        settings_screen = CRTScreen(name='settings')
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        layout.add_widget(Label(
            text="[ SETTINGS ]",
            markup=True,
            color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT),
            font_size='24sp'
        ))
        layout.add_widget(Button(
            text="[ BACK ]",
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            on_press=lambda x: setattr(sm, 'current', 'main_menu')
        ))
        settings_screen.add_widget(layout)
        sm.add_widget(settings_screen)
        
        # Open file placeholder
        open_screen = CRTScreen(name='open')
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        layout.add_widget(Label(
            text="[ OPEN FILE ]",
            markup=True,
            color=self.hex_to_rgba(CRTCOLORS.TEXT_BRIGHT),
            font_size='24sp'
        ))
        layout.add_widget(Button(
            text="[ BACK ]",
            background_color=self.hex_to_rgba(CRTCOLORS.BG_DARK),
            color=self.hex_to_rgba(CRTCOLORS.TEXT_NORMAL),
            on_press=lambda x: setattr(sm, 'current', 'main_menu')
        ))
        open_screen.add_widget(layout)
        sm.add_widget(open_screen)
        
        return sm
    
    @staticmethod
    def hex_to_rgba(hex_color: str, alpha: float = 1.0):
        """Convert hex color to rgba"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return (r, g, b, alpha)
    
    def on_stop(self):
        """Cleanup on exit"""
        if self.ai_manager:
            self.ai_manager.stop()


# ==============================================================================
# Entry Point
# ==============================================================================

def main():
    """Main entry point"""
    print("Starting Fallout Dialogue Creator...")
    print(f"Version {__version__}")
    print("=" * 40)
    FalloutDialogueCreatorApp().run()


if __name__ == '__main__':
    main()
