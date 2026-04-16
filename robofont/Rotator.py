import vanilla
from mojo.UI import CurrentGlyphWindow
from mojo.roboFont import CurrentGlyph
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from AppKit import NSTextAlignmentCenter
import math

class Rotator:
    def __init__(self):
        self.num_copies = 5
        self.axis_position = 4  # center (middle of 3x3 grid, 0-indexed)

        # Compact window
        self.w = vanilla.FloatingWindow((93, 140), "Rotator")

        # 3x3 grid of radio buttons for axis selection
        # Layout: top-left, top-center, top-right
        #         center-left, center, center-right
        #         bottom-left, bottom-center, bottom-right
        grid_size = 30
        grid_start_x = 15
        grid_start_y = 3

        axis_positions = [
            # Row 1
            (grid_start_x, grid_start_y),                          # top-left
            (grid_start_x + grid_size, grid_start_y),              # top-center
            (grid_start_x + grid_size * 2, grid_start_y),          # top-right
            # Row 2
            (grid_start_x, grid_start_y + grid_size),              # center-left
            (grid_start_x + grid_size, grid_start_y + grid_size),  # center
            (grid_start_x + grid_size * 2, grid_start_y + grid_size), # center-right
            # Row 3
            (grid_start_x, grid_start_y + grid_size * 2),          # bottom-left
            (grid_start_x + grid_size, grid_start_y + grid_size * 2), # bottom-center
            (grid_start_x + grid_size * 2, grid_start_y + grid_size * 2), # bottom-right
        ]

        self.axis_buttons = []
        for i, (x, y) in enumerate(axis_positions):
            btn = vanilla.RadioButton((x, y, 20, 20), "",
                                     callback=self.updateAxis,
                                     sizeStyle="small")
            setattr(self.w, f"axis_{i}", btn)
            self.axis_buttons.append(btn)

        # Set center as default
        self.axis_buttons[4].set(True)

        self.w.copiesValue = vanilla.EditText((10, 87, -10, 22),
                                             str(self.num_copies),
                                             callback=self.updateCopiesText,
                                             sizeStyle="small")
        self.w.copiesValue.getNSTextField().setAlignment_(NSTextAlignmentCenter)

        # Apply button
        self.w.applyButton = vanilla.Button((10, 112, -10, 22),
                                           "Rotate",
                                           callback=self.applyRotation,
                                           sizeStyle="small")

        self.w.open()

    def updateAxis(self, sender):
        # Find which button was clicked
        for i, btn in enumerate(self.axis_buttons):
            if btn == sender:
                self.axis_position = i
                # Uncheck all others
                for j, other_btn in enumerate(self.axis_buttons):
                    if i != j:
                        other_btn.set(False)
                break

    def updateCopiesText(self, sender):
        try:
            value = int(sender.get())
            if value >= 2:
                self.num_copies = value
            else:
                sender.set(str(self.num_copies))
        except ValueError:
            sender.set(str(self.num_copies))

    def getAxisPoint(self, bounds):
        """Calculate the axis point based on bounds and selected position."""
        xMin, yMin, xMax, yMax = bounds

        # Map axis_position (0-8) to coordinates
        # 0=TL, 1=TC, 2=TR, 3=CL, 4=C, 5=CR, 6=BL, 7=BC, 8=BR
        row = self.axis_position // 3  # 0=top, 1=center, 2=bottom
        col = self.axis_position % 3   # 0=left, 1=center, 2=right

        # Calculate x
        if col == 0:   # left
            x = xMin
        elif col == 1: # center
            x = (xMin + xMax) / 2.0
        else:          # right
            x = xMax

        # Calculate y
        if row == 0:   # top
            y = yMax
        elif row == 1: # center
            y = (yMin + yMax) / 2.0
        else:          # bottom
            y = yMin

        return (x, y)

    def applyRotation(self, sender):
        glyph = CurrentGlyph()
        if not glyph:
            print("No glyph selected")
            return

        if not glyph.selection:
            print("No contours or components selected")
            return

        # Get selected contours
        selected_contours = [c for c in glyph if c.selected]
        if not selected_contours:
            print("No contours selected")
            return

        # Calculate bounds of selection
        all_points = []
        for contour in selected_contours:
            for point in contour.points:
                all_points.append((point.x, point.y))

        if not all_points:
            return

        xMin = min(p[0] for p in all_points)
        xMax = max(p[0] for p in all_points)
        yMin = min(p[1] for p in all_points)
        yMax = max(p[1] for p in all_points)
        bounds = (xMin, yMin, xMax, yMax)

        # Get rotation axis point
        axis_x, axis_y = self.getAxisPoint(bounds)

        # Calculate rotation angle for each copy
        angle_step = 360.0 / self.num_copies

        # Record the selected contours once, then replay them through
        # transformed segment pens to append rotated copies to the glyph.
        pen = RecordingPen()
        for contour in selected_contours:
            contour.draw(pen)

        glyph.prepareUndo("Rotate Copies")

        # Create rotated copies
        for i in range(1, self.num_copies):
            angle_deg = angle_step * i
            angle_rad = math.radians(angle_deg)

            # Create rotation matrix around axis point
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            # Translation to origin, rotation, translation back
            dx = axis_x - (axis_x * cos_a - axis_y * sin_a)
            dy = axis_y - (axis_x * sin_a + axis_y * cos_a)

            transform = (cos_a, sin_a, -sin_a, cos_a, dx, dy)

            transform_pen = TransformPen(glyph.getPen(), transform)
            pen.replay(transform_pen)

        glyph.performUndo()
        glyph.changed()

if __name__ == "__main__":
    Rotator()
