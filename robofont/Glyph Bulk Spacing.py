# menuTitle : (Menu) Glyph Bulk Spacing

from mojo.subscriber import Subscriber, registerFontOverviewSubscriber
from mojo.UI import PostBannerNotification, AskString
from fontTools.misc.fixedTools import otRound
from statistics import median
import vanilla

class GlyphBulkSpacingMenu(Subscriber):
    
    '''
    2024.06.16
    Peter Laxalt
    '''

    def build(self):
        self.f = None
        
    def fontOverviewWantsContextualMenuItems(self, info):
        self.f = CurrentFont()

        if self.f.selectedGlyphNames and len(self.f.selectedGlyphNames) != len(self.f.keys()):
            self.message = "Glyph Bulk Spacing"
            self.span = self.f.selectedGlyphNames
            
        menu_items = [
                (self.message, [
                    ('Set spacing of selected glyphs', self.set_spacing),
                    ]
                )
            ]
        info['itemDescriptions'].extend(menu_items)
        
    def set_spacing(self, sender):
        # Create the dialog window
        self.w = vanilla.Window((300, 130), "Set Glyph Spacing")
        
        # Add checkbox and input fields for left spacing
        self.w.checkbox_left = vanilla.CheckBox((10, 10, 20, 20), "", value=True, callback=self.toggle_left_spacing)
        self.w.text_left = vanilla.TextBox((35, 10, 80, 20), "Left Spacing:")
        self.w.input_left = vanilla.EditText((125, 10, 50, 20), "0")
        
        # Add checkbox and input fields for right spacing
        self.w.checkbox_right = vanilla.CheckBox((10, 40, 20, 20), "", value=True, callback=self.toggle_right_spacing)
        self.w.text_right = vanilla.TextBox((35, 40, 80, 20), "Right Spacing:")
        self.w.input_right = vanilla.EditText((125, 40, 50, 20), "20")
        
        # Add warning message (hidden by default)
        self.w.warning_text = vanilla.TextBox((10, 70, 280, 20), "⚠️ Select at least one spacing option", sizeStyle="small")
        self.w.warning_text.show(False)
        
        # Add Apply button
        self.w.apply_button = vanilla.Button((150, 100, 140, 20), "✅ Apply", callback=self.update_glyphs)
        self.w.cancel_button = vanilla.Button((10, 100, 140, 20), "⛔️ Cancel", callback=self.cancel)
        
        # Open the window
        self.w.open()
    
    def toggle_left_spacing(self, sender):
        is_enabled = sender.get()
        self.w.input_left.enable(is_enabled)
        if not is_enabled:
            self.w.input_left.set("")
        else:
            self.w.input_left.set("0")
        self.update_apply_button_state()
    
    def toggle_right_spacing(self, sender):
        is_enabled = sender.get()
        self.w.input_right.enable(is_enabled)
        if not is_enabled:
            self.w.input_right.set("")
        else:
            self.w.input_right.set("20")
        self.update_apply_button_state()
    
    def update_apply_button_state(self):
        left_enabled = self.w.checkbox_left.get()
        right_enabled = self.w.checkbox_right.get()
        has_selection = left_enabled or right_enabled
        self.w.apply_button.enable(has_selection)
        self.w.warning_text.show(not has_selection)

    def cancel(self, sender):
        self.w.close()

    def update_glyphs(self, sender):
        
        # Check if there is a font open
        if self.f is not None:
            try:
                apply_left = self.w.checkbox_left.get()
                apply_right = self.w.checkbox_right.get()
                
                margin_left = int(self.w.input_left.get()) if apply_left else None
                margin_right = int(self.w.input_right.get()) if apply_right else None
                
                for g_name in self.span:
                    g = self.f[g_name]
                    
                    if apply_left:
                        g.leftMargin = margin_left
                    if apply_right:
                        g.rightMargin = margin_right

                self.w.close()
                self.f.changed()
                
                # Build message based on what was applied
                parts = []
                if apply_left:
                    parts.append(f"left {margin_left}")
                if apply_right:
                    parts.append(f"right {margin_right}")
                message = f"Spacing applied to all glyphs: {', '.join(parts)}."
                PostBannerNotification(message, 2)  # Show success message for 2 seconds

            except ValueError:
                print("Invalid input. Please enter integer values.")
        else:
            print("No font open")
        
        
#===================
        
if __name__ == "__main__":    
    registerFontOverviewSubscriber(GlyphBulkSpacingMenu)