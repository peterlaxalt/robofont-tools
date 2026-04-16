from glyphNameFormatter.reader import *

allUnis = list(uni2name.keys())
font = CurrentFont()

# Look up glyphs
glyphsLookup = [
    'Ḡ', 'Ḫ', 'Ḹ', 'Ṃ', 'Ṝ', 'Ṡ', 'Ẏ', 'ḡ', 'ḫ', 'ḹ', 'ṃ', 'ṝ', 'ṡ', 'ẏ', '―', '«', '»'
]


# Mark True to add them to font
addToFont = True


# Let it rip
for v in allUnis:
    
    for i in glyphsLookup:
        if chr(v) == i:
            print(hex(v), chr(v), u2n(v), u2r(v))
            
            if addToFont == True:
                glyphName = u2n(v)
                font.newGlyph(glyphName, clear=False)
                font.getGlyph(glyphName).autoUnicodes()
                print(font.getGlyph(glyphName))
