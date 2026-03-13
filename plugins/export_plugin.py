"""
Export Plugin for Fallout Dialogue Creator

This plugin provides export functionality for .ssl (script) and .msg (message) files
used by the Fallout 2 engine. These files are exported to the configured directories
and can be compiled/used by the Fallout 2 game engine.
"""

from core.plugin_system import PluginInterface, PluginType, PluginHooks, PluginInfo
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ExportPlugin(PluginInterface):
    """Plugin for exporting dialogue data to Fallout 2 compatible formats"""

    def __init__(self):
        super().__init__()
        self.plugin_info = PluginInfo(
            name="Export Plugin",
            version="1.0.0",
            description="Exports dialogue data to .ssl and .msg files for Fallout 2",
            author="Fallout Dialogue Creator Team",
            plugin_type=PluginType.EXPORT_EXTENSION
        )
        self.menu_action_ssl = None
        self.menu_action_msg = None
        self.dialog_manager = None
        self.settings = None

    def initialize(self, plugin_manager):
        """Initialize the plugin"""
        logger.info("Initializing Export Plugin")
        return True

    def activate(self):
        """Activate the plugin"""
        logger.info("Activating Export Plugin")
        return True

    def deactivate(self):
        """Deactivate the plugin"""
        logger.info("Deactivating Export Plugin")
        if self.menu_action_ssl:
            # Remove menu actions if they exist
            pass
        if self.menu_action_msg:
            pass
        return True

    def get_hooks(self):
        """Return hook functions"""
        return {
            PluginHooks.APP_STARTUP: [self.on_app_startup],
            PluginHooks.UI_MENU_BAR_CREATED: [self.on_menu_bar_created],
            PluginHooks.DIALOGUE_LOADED: [self.on_dialogue_loaded],
        }

    def on_app_startup(self, app):
        """Called when application starts"""
        logger.info("Export Plugin: Application startup detected")

    def on_menu_bar_created(self, menu_bar):
        """Called when menu bar is created - add our export menu items"""
        logger.info("Export Plugin: Adding export menu items")

        # Find the Tools menu
        tools_menu = None
        for action in menu_bar.actions():
            if action.text() == "&Tools":
                tools_menu = action.menu()
                break

        if tools_menu:
            # Add separator and our export actions
            tools_menu.addSeparator()

            # Export SSL submenu
            export_menu = tools_menu.addMenu("Export")

            self.menu_action_ssl = export_menu.addAction("Export .ssl Script")
            self.menu_action_ssl.triggered.connect(self.export_ssl)

            self.menu_action_msg = export_menu.addAction("Export .msg Messages")
            self.menu_action_msg.triggered.connect(self.export_msg)

    def on_dialogue_loaded(self, dialogue):
        """Called when a dialogue is loaded"""
        logger.info(f"Export Plugin: Dialogue loaded - {dialogue.npcname}")

    def export_ssl(self):
        """Export dialogue scripts to .ssl format"""
        try:
            logger.info("Export Plugin: Exporting SSL scripts")

            # Get access to dialog manager through the plugin system
            # This is a bit of a hack - in a real implementation we'd have better access
            from core.dialog_manager import DialogManager
            dialog_manager = None

            # Try to find dialog manager instance
            import gc
            for obj in gc.get_objects():
                if isinstance(obj, DialogManager):
                    dialog_manager = obj
                    break

            if not dialog_manager:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Export Error", "Could not access dialogue manager")
                return

            dialogue = dialog_manager.get_current_dialogue()
            if not dialogue:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Export Error", "No dialogue loaded")
                return

            # Generate SSL content
            ssl_content = self._generate_ssl_content(dialogue)

            # Get output path
            ssl_filename = self._get_ssl_filename(dialogue)
            output_path = Path("script_output") / ssl_filename

            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ssl_content)

            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                None,
                "Export Complete",
                f"SSL script exported successfully!\n\n"
                f"File: {output_path}\n"
                f"Size: {len(ssl_content)} characters\n\n"
                f"This file can be compiled with the Fallout 2 script compiler."
            )

        except Exception as e:
            logger.error(f"Error exporting SSL: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Export Error", f"Failed to export SSL files:\n{str(e)}")

    def export_msg(self):
        """Export dialogue messages to .msg format"""
        try:
            logger.info("Export Plugin: Exporting MSG messages")

            # Get access to dialog manager
            from core.dialog_manager import DialogManager
            dialog_manager = None

            import gc
            for obj in gc.get_objects():
                if isinstance(obj, DialogManager):
                    dialog_manager = obj
                    break

            if not dialog_manager:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Export Error", "Could not access dialogue manager")
                return

            dialogue = dialog_manager.get_current_dialogue()
            if not dialogue:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Export Error", "No dialogue loaded")
                return

            # Generate MSG content
            msg_content = self._generate_msg_content(dialogue)

            # Get output path - use the Fallout 2 dialog directory
            msg_filename = self._get_msg_filename(dialogue)
            output_path = Path("E:\\Games\\Fallout2\\data2\\text\\english\\dialog") / msg_filename

            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(msg_content)

            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                None,
                "Export Complete",
                f"MSG file exported successfully!\n\n"
                f"File: {output_path}\n"
                f"Size: {len(msg_content)} characters\n\n"
                f"This file contains dialogue text for Fallout 2."
            )

        except Exception as e:
            logger.error(f"Error exporting MSG: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Export Error", f"Failed to export MSG files:\n{str(e)}")

    def _get_ssl_filename(self, dialogue):
        """Generate SSL filename from dialogue"""
        # Use NPC name, replace spaces/special chars with underscores
        name = dialogue.npcname.lower().replace(' ', '_').replace('-', '_')
        return f"{name}.ssl"

    def _generate_ssl_content(self, dialogue):
        """Generate SSL script content from dialogue"""
        from datetime import datetime

        # Generate node headers
        node_headers = []
        node_procs = []
        for i, node in enumerate(dialogue.nodes):
            node_headers.append(f"procedure Node{i};")
            # Generate basic node procedure
            node_procs.append(f"""procedure Node{i} begin
   gsay_reply(0, {100 + i});
   giq_option(0, 0, gsay_reply, 0);
end""")

        # Generate skill check headers and procedures (placeholder)
        skill_check_headers = "// Skill check procedures\n// procedure CheckSkill_SmallGuns;\n"
        skill_check_procs = "// Skill check implementations\n// procedure CheckSkill_SmallGuns begin\n// end\n"

        # Generate custom procedure headers and procedures
        custom_proc_headers = []
        custom_procs = []
        for proc in dialogue.customprocs:
            custom_proc_headers.append(f"procedure {proc.name};")
            custom_procs.append(f"procedure {proc.name} begin\n{proc.lines}\nend")

        # Generate variables
        variables = []
        for var in dialogue.variables:
            variables.append(f"#define LVAR_{var.name.upper()} ({var.value})")

        # Fill in the template
        template = '''/*

        Name:           ##NAME##
        Location:       ##LOCATION##
        Description:    ##DESCRIPTION##

           Created: ##CREATIONDATE##

*/

/* Include Files */


//Overrides the pickup p proc.
//#define NPC_REACTION_TYPE       REACTION_TC /* REACTION_TC REACTION_TG REACTION_C REACTION_G */
#define NPC_REACTION_VAR        7 /* same as thief variable */

#include "##HEADERS_PATH##\\define.h"
//#include "##HEADERS_PATH##\\<TownName.h>"

#define NAME                    SCRIPT_##SCRNUM##

// NOTE: This is set to 0 by default
#define TOWN_REP_VAR            (0)

#include "##HEADERS_PATH##\\command.h"
#include "##HEADERS_PATH##\\ModReact.h"

/* Helper macros */

variable temp;

/* Standard Script Procedures */
procedure start;
procedure critter_p_proc;
procedure pickup_p_proc;
procedure talk_p_proc;
procedure destroy_p_proc;
procedure look_at_p_proc;
procedure description_p_proc;
procedure use_skill_on_p_proc;
procedure damage_p_proc;
procedure map_enter_p_proc;
procedure timed_event_p_proc;


/* Script Specific Procedure Calls */
procedure Node998;                                      // This Node is Always Combat
procedure Node999;                                      // This Node is Always Ending

##SKILLCHECKHEADERS##
##CUSTOMPROCHEADERS##


// The next lines are added in by the Designer Tool.
// Do NOT add in any lines here.
//~~~~~~~~~~~~~~~~ DESIGNER TOOL STARTS HERE

##NODEHEADERS##

//~~~~~~~~~~~~~~~~ DESIGN TOOL ENDS HERE
// The Following lines are for anything that is not needed to be
// seen by the design Tool


/* Local Variables which are saved. All Local Variables need to be
   prepended by LVAR_ */
#define LVAR_Herebefore                 (4)
#define LVAR_Hostile                    (5)
#define LVAR_Personal_Enemy             (6)
#define LVAR_Caught_Thief               (7)

##VARIABLES##

/* Imported variables from the Map scripts. These should only be
   pointers and variables that need not be saved. If a variable
   Needs to be saved, make it a map variable (MVAR_) */


/* Local variables which do not need to be saved between map changes. */
variable Only_Once:=0;

procedure start begin
end

/* This procedure will get called each time that the map is first entered. It will
   set up the Team number and AI packet for this critter. This will override the
   default from the prototype, and needs to be set in scripts. */
procedure map_enter_p_proc begin
   Only_Once:=0;
//   critter_add_trait(self_obj,TRAIT_OBJECT,OBJECT_TEAM_NUM,TEAM_);
//   critter_add_trait(self_obj,TRAIT_OBJECT,OBJECT_AI_PACKET,AI_);
end


/* Every heartbeat that the critter gets, this procedure will be called. Anything from
   Movement to attacking the player on sight can be placed in here.*/
procedure critter_p_proc begin

/* If the critter is mad at the player for any reason, it will attack and remember to attack
   the player should the game be saved and loaded repeatedly. Additionally, if any special
   actions need to be taken by the critter based on previous combat, the critter will remember
   this as well. */

   if ((local_var(LVAR_Hostile) != 0) and (obj_can_see_obj(self_obj,dude_obj))) then begin
       set_local_var(LVAR_Hostile,1);
       self_attack_dude;
       //Macro made by Tom to keep the critter fleeing.
   end

end

/* Whenever the critter takes damage of any type, this procedure will be called. Things
   like setting ENEMY_ and LVAR_Personal_Enemy can be set here. */
procedure damage_p_proc begin

/* If the player causes damage to this critter, then he will instantly consider the player
   his personal enemy. In Critter_Proc or through dialog, actions will be taken against
   the player for his evil acts. */
   if (obj_in_party(source_obj)) then begin
       set_local_var(LVAR_Personal_Enemy,1);
   end

end

/* Any time that the player is caught stealing from this critter, Pickup_proc will be called.
   In here, various things can happen. The most common response is instant hostility which
   will be remembered. */
procedure pickup_p_proc begin
   if (source_obj == dude_obj) then begin
       set_local_var(LVAR_Hostile,2);
   end
end

/* The dialog system is setup and prepares the player to talk to this NPC. Where To Go
   written by designers are placed in here. Additionally, Reactions are generated and
   stored which affects player interactions. */
procedure talk_p_proc begin

##LOCALVARDEBUG##

   Evil_Critter:=0;
   Slavery_Tolerant:=SLAVE_TOLERANT;
   Karma_Perception:=KARMA_PERCEPTION1;

   CheckKarma;

   GetReaction;

##TALKPROCCODE##

end

procedure timed_event_p_proc begin
end

/* This procedure gets called only on the death of this NPC. Special things like
   incrementing the death count for reputation purposes and Enemy Counters are placed
   in here. */
procedure destroy_p_proc begin

/* Increment the aligned critter counter*/
   inc_good_critter
/* inc_evil_critter */
/* inc_neutral_critter */

/* Set global_variable for Enemy status*/
end

/* Look_at_p_proc gets called any time that the player passes the cursor over any object.
   This should only hold the most cursory of glances for the player. */
procedure look_at_p_proc begin
   script_overrides;
   if (local_var(LVAR_Herebefore) == 0) then
      display_mstr(100);
   else
      display_mstr(101);
end

/* The player will see more indepth descriptions from this procedure. They are actively
   looking at the critter and want more information. Things like names can be added here
   if the critter is known to the player. */
procedure description_p_proc begin
   script_overrides;
   display_mstr(102);
end

/* Any time a skill is used on a critter this call is made. This can be to give examinations
   for things like Doctor skill or messages for various other skills. */
procedure use_skill_on_p_proc begin
end

/* Should the Player ever cause the NPC too much discomfort that he desires to attack the player,
   this call will be made. Essentially, it stores the Hostile vaule so that the critter remembers
   he was once hostile towards the player.*/
procedure Node998 begin
   set_local_var(LVAR_Hostile,2);
end

/* Anytime that there is a need for an ending to dialog, this node is to be called. It will just
   exit from the dialog system without any reprisals from the NPC. */
procedure Node999 begin
debug_msg("LVAR_Herebefore == "+local_var(LVAR_Herebefore));
if (local_var(LVAR_Herebefore)==0) then
begin
set_local_var(LVAR_Herebefore,1);
end
end

// Skill checks and miscellaneous procedures

##SKILLCHECKPROCS##

##CUSTOMPROCS##

// Not lines are allowed to be added below here
// The Following lines are from the Design Tool
//~~~~~~~~~~~~~~~~ DESIGN TOOL STARTS HERE

##NODEPROCS##

//xxxxxxxxxxxxxxxxxxxx'''

        # Replace placeholders
        content = template.replace('##NAME##', dialogue.npcname)
        content = content.replace('##LOCATION##', dialogue.location or 'Unknown')
        content = content.replace('##DESCRIPTION##', dialogue.description or 'No description')
        content = content.replace('##CREATIONDATE##', datetime.now().strftime('%Y-%m-%d'))
        content = content.replace('##HEADERS_PATH##', 'headers')  # Default path
        content = content.replace('##SCRNUM##', '001')  # Default script number
        content = content.replace('##SKILLCHECKHEADERS##', skill_check_headers)
        content = content.replace('##CUSTOMPROCHEADERS##', '\n'.join(custom_proc_headers))
        content = content.replace('##NODEHEADERS##', '\n'.join(node_headers))
        content = content.replace('##VARIABLES##', '\n'.join(variables))
        content = content.replace('##LOCALVARDEBUG##', '   // Local variable debug info')
        content = content.replace('##TALKPROCCODE##', '   start_gdialog(NAME, self_obj, 4, -1, -1);\n   gsay_start;\n   call Node0;  // Start with first node\n   gsay_end;\n   end_dialogue;')
        content = content.replace('##SKILLCHECKPROCS##', skill_check_procs)
        content = content.replace('##CUSTOMPROCS##', '\n\n'.join(custom_procs))
        content = content.replace('##NODEPROCS##', '\n\n'.join(node_procs))

        return content

    def _get_msg_filename(self, dialogue):
        """Generate MSG filename from dialogue"""
        # Use NPC name, replace spaces/special chars with underscores
        name = dialogue.npcname.lower().replace(' ', '_').replace('-', '_')
        return f"{name}.msg"

    def _generate_msg_content(self, dialogue):
        """Generate MSG file content from dialogue"""
        lines = []

        # MSG file header
        lines.append("{100}{}{}")
        lines.append("{101}{}{}")
        lines.append("{102}{}{}")

        # Add dialogue nodes (starting from 103)
        msg_id = 103
        for node in dialogue.nodes:
            # NPC text
            if node.npctext:
                lines.append(f"{{{msg_id}}}{{{node.npctext}}}")
                msg_id += 1

            # Player options
            for option in node.options:
                if option.optiontext:
                    lines.append(f"{{{msg_id}}}{{{option.optiontext}}}")
                    msg_id += 1

        # Add float messages if available (placeholder for now)
        # In a full implementation, this would include float messages from the dialogue

        return '\n'.join(lines) + '\n'