import vanilla
from AppKit import NSFont, NSFontManager, NSFontAttributeName, NSParagraphStyleAttributeName, NSMutableParagraphStyle, NSAttributedString, NSPasteboard
from mojo.UI import CurrentGlyphWindow
from mojo.roboFont import CurrentFont
from mojo.events import addObserver, removeObserver

FONT_SIZE = 100

class ReferenceCharacterWindowV2:
    def __init__(self):
        self.fonts = self.getSystemFonts()
        self.useCurrentGlyphMode = False
        self.font_name = "NotoSansJP-Bold" if "NotoSansJP-Bold" in self.fonts else (self.fonts[0] if self.fonts else "")
        self.character = "う"
        self.left_compare = ""
        self.right_compare = ""
        self.min_width = 300

        font = NSFont.fontWithName_size_(self.font_name, FONT_SIZE)
        if font:
            text_size = self.calculateTextSize(self.character, font)
            initial_width = max(int(text_size.width) + 40, self.min_width)
            initial_height = int(text_size.height) + 108
        else:
            initial_width = self.min_width
            initial_height = 240

        self.w = vanilla.FloatingWindow((initial_width, initial_height), "Reference Character Viewer v2")

        # ── Top: font picker ─────────────────────────────────────────────────
        self.w.fontInput = vanilla.PopUpButton((10, 8, -10, 24), self.fonts, callback=self.updateFont)

        # ── Middle: character preview ─────────────────────────────────────────
        # textBox fills between fontInput and the two bottom rows
        self.w.textBox = vanilla.TextBox((10, 32, -10, -68), "", alignment="center")

        # Copy button overlaid top-right of the preview area
        self.w.copyButton = vanilla.Button((-126, 36, 116, 22), "Copy current glyph", sizeStyle="small", callback=self.copyCharacter)

        # ── Second-to-last row: main text input ───────────────────────────────
        self.w.characterInput = vanilla.EditText((10, -58, -10, 24), self.character, callback=self.updateCharacter)

        # ── Bottom row: [x] current glyph   Compare glyph [L___] [R___] ───
        #
        # All controls share a visual center line at ~19px from the window bottom.
        # Each control uses its natural height for sizeStyle="small" so macOS
        # top-aligns them correctly onto that shared center:
        #
        #   CheckBox  natural h≈18 → y=-28, h=18  → center at H-19  ✓
        #   TextBox   natural h≈14 → y=-26, h=14  → center at H-19  ✓
        #   EditText  natural h≈19 → y=-28, h=19  → center at H-18.5 ✓
        #
        # Layout right-to-left from right edge (10px padding):
        #   rightInput    : 40px → x=-50
        #   5px gap
        #   leftInput     : 45px → x=-100
        #   5px gap
        #   "Compare glyph": 85px → x=-190
        #   5px gap
        #   checkbox      : fills left → (10, y, -195, h)
        #
        self.w.useGlyphCheckbox = vanilla.CheckBox((10, -28, -195, 18), "Current glyph", sizeStyle="small", callback=self.toggleUseCurrentGlyph)
        self.w.compareLabel = vanilla.TextBox((-165, -26, 85, 14), "Neighbors", sizeStyle="small")
        self.w.leftInput = vanilla.EditText((-100, -28, 45, 19), "", sizeStyle="small", callback=self.updateLeftCompare, placeholder="Before")
        self.w.rightInput = vanilla.EditText((-50, -28, 40, 19), "", sizeStyle="small", callback=self.updateRightCompare, placeholder="After")

        if "NotoSansJP-Bold" in self.fonts:
            self.w.fontInput.set(self.fonts.index("NotoSansJP-Bold"))

        addObserver(self, "onGlyphChanged", "currentGlyphChanged")
        addObserver(self, "onGlyphChanged", "fontWindowSelectionChanged")

        self.w.bind("close", self.windowClosed)
        self.updateDisplay()
        self.w.open()

    def windowClosed(self, sender):
        removeObserver(self, "currentGlyphChanged")
        removeObserver(self, "fontWindowSelectionChanged")

    def copyCharacter(self, sender):
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(self.character, "public.utf8-plain-text")

    # -------------------------------------------------------------------------
    # Checkbox + glyph tracking

    def toggleUseCurrentGlyph(self, sender):
        self.useCurrentGlyphMode = bool(sender.get())
        self.w.characterInput.enable(not self.useCurrentGlyphMode)
        if self.useCurrentGlyphMode:
            self.updateFromCurrentGlyph()
        else:
            # Collapse exactly what was on screen into the main input
            full = self.left_compare + self.character + self.right_compare
            self.character = full
            self.left_compare = ""
            self.right_compare = ""
            self.w.characterInput.set(full)
            self.w.leftInput.set("")
            self.w.rightInput.set("")
            self.updateDisplay()

    def onGlyphChanged(self, info):
        if self.useCurrentGlyphMode:
            self.updateFromCurrentGlyph()

    def updateFromCurrentGlyph(self):
        glyph = None
        glyph_window = CurrentGlyphWindow()
        if glyph_window:
            glyph = glyph_window.getGlyph()
        if glyph is None:
            font = CurrentFont()
            if font:
                selected = font.selectedGlyphs
                if selected:
                    glyph = selected[0]
        if glyph is None:
            return
        uni = glyph.unicode
        if uni is None:
            return
        try:
            char = chr(int(uni, 16)) if isinstance(uni, str) else chr(uni)
            self.character = char
            self.w.characterInput.set(self.character)
            self.updateDisplay()
        except (ValueError, TypeError):
            pass

    # -------------------------------------------------------------------------
    # Input callbacks

    def updateCharacter(self, sender):
        self.character = sender.get()
        self.updateDisplay()

    def updateLeftCompare(self, sender):
        self.left_compare = sender.get()
        self.updateDisplay()

    def updateRightCompare(self, sender):
        self.right_compare = sender.get()
        self.updateDisplay()

    def updateFont(self, sender=None):
        index = self.w.fontInput.get()
        self.font_name = self.fonts[index]
        self.updateDisplay()

    # -------------------------------------------------------------------------
    # Display

    def updateDisplay(self):
        try:
            font = NSFont.fontWithName_size_(self.font_name, FONT_SIZE)
            if not font:
                raise ValueError(f"Font '{self.font_name}' not found.")

            display_text = self.left_compare + self.character + self.right_compare

            attributes = {
                NSFontAttributeName: font,
                NSParagraphStyleAttributeName: self.centeredParagraphStyle(),
            }
            attrString = NSAttributedString.alloc().initWithString_attributes_(display_text, attributes)
            self.w.textBox.set(attrString)

            # Height always fits content; width only expands, never shrinks
            text_size = self.calculateTextSize(display_text, font)
            new_width = max(int(text_size.width) + 40, self.min_width)
            new_height = int(text_size.height) + 108
            x, y, current_width, _ = self.w.getPosSize()
            self.w.setPosSize((x, y, max(new_width, current_width), new_height))

        except Exception as e:
            self.w.textBox.set(f"Error: {e}")

    # -------------------------------------------------------------------------
    # Helpers

    def centeredParagraphStyle(self):
        style = NSMutableParagraphStyle.alloc().init()
        style.setAlignment_(1)
        return style

    def calculateTextSize(self, text, font):
        attrs = {NSFontAttributeName: font}
        return NSAttributedString.alloc().initWithString_attributes_(text, attrs).size()

    def getSystemFonts(self):
        manager = NSFontManager.sharedFontManager()
        return [f for f in manager.availableFonts() if not f.startswith(".")]

if __name__ == "__main__":
    ReferenceCharacterWindowV2()
