# terminal.py

import tkinter as tk
from typing import Optional, Tuple, Dict, Any

# Assuming these modules exist and contain the necessary classes
from cursor import Position, CursorController
from memory import PixelMemory, EncodingMode
from settings import SETTINGS # Import SETTINGS to access blink_rate directly

class TerminalCanvas(tk.Canvas):
    def __init__(self, master, canvas_width, canvas_height, char_size, font):
        super().__init__(master, width=canvas_width, height=canvas_height, bg="black", highlightthickness=0)
        self.pack(fill=tk.BOTH, expand=True)

        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.char_width = char_size
        self.char_height = char_size
        self.font = font

        self.columns = canvas_width // self.char_width
        self.lines = canvas_height // self.char_height

        self.cursor_controller: Optional[CursorController] = None
        self.pixel_memory: Optional[PixelMemory] = None # Member to store the PixelMemory instance

        self.cursor_rect_id = None
        self.blink_id = None
        self.is_cursor_visible = True

        self._start_cursor_blink()

        self.status_label_id: Optional[int] = None # To manage status text on canvas

    def set_cursor_controller(self, controller: CursorController) -> None:
        """Sets the cursor controller for the terminal."""
        self.cursor_controller = controller
        self.cursor_controller.set_canvas_dimensions(self.columns, self.lines)

    def set_pixel_memory(self, memory: PixelMemory) -> None:
        """Sets the PixelMemory instance for the terminal to interact with."""
        self.pixel_memory = memory

    def _start_cursor_blink(self):
        # Use the blink_rate from SETTINGS
        blink_rate = SETTINGS.get("blink_rate", 500) # Default to 500ms if not found

        if self.blink_id:
            self.after_cancel(self.blink_id)
        self.blink_id = self.after(blink_rate, self._blink_cursor)

    def _blink_cursor(self):
        if self.cursor_controller:
            if self.is_cursor_visible:
                self.delete(self.cursor_rect_id)
            else:
                self.update_cursor_position(visible=True)
            self.is_cursor_visible = not self.is_cursor_visible

        blink_rate = SETTINGS.get("blink_rate", 500)
        self.blink_id = self.after(blink_rate, self._blink_cursor)

    def update_cursor_position(self, visible: bool = True) -> None:
        """Draws or redraws the cursor rectangle."""
        if not self.cursor_controller:
            return

        self.delete(self.cursor_rect_id) # Delete old cursor

        if visible:
            x, y = self.cursor_controller.get_pixel_coords()
            self.cursor_rect_id = self.create_rectangle(
                x, y, x + self.char_width, y + self.char_height,
                outline="white", width=1
            )
        self.is_cursor_visible = visible

    def draw_char_at_cursor(self, char: str, color: str, tag: Optional[str] = None) -> None:
        """Draws a character at the current cursor position on the canvas."""
        if not self.cursor_controller:
            return

        x, y = self.cursor_controller.get_pixel_coords()
        # Delete any existing char at this specific grid position
        # We'll use a tag based on line and column for more precise deletion
        char_tag = f"char_{self.cursor_controller.current_line}_{self.cursor_controller.current_column}"
        self.delete(char_tag) # Delete any text at this position

        final_tags = [char_tag]
        if tag:
            final_tags.append(tag)

        self.create_text(
            x, y,
            text=char,
            font=self.font,
            fill=color,
            anchor="nw",
            tags=tuple(final_tags) # Apply tags for deletion and identification
        )

        # TODO: If you intend to draw to pixel memory, this is where you'd call
        # self.pixel_memory.set_pixel(...) for each pixel of the character's glyph.
        # This is a more advanced feature for a true "pixel OS".

    def write_line(self, text: str, line_num: Optional[int] = None) -> None:
        """Writes a line of text to the terminal, handling scrolling and cursor updates."""
        if not self.cursor_controller:
            return

        # If line_num is provided, set cursor to that line, otherwise use current line
        target_line = line_num if line_num is not None else self.cursor_controller.current_line

        # Ensure the target line exists within the visible screen area
        if target_line >= self.lines:
            # If writing beyond visible lines, scroll up until target_line is visible
            scroll_needed = target_line - (self.lines - 1)
            for _ in range(scroll_needed):
                self._scroll_up()
            self.cursor_controller.current_line = self.lines - 1 # Adjust cursor line after scroll
            target_line = self.lines - 1 # Update target line to the new visible line

        # Move cursor to the start of the target line
        self.cursor_controller.set_position_by_line_col(target_line, 0)

        self.clear_line(target_line) # Clear the line before writing new content

        for char_index, char in enumerate(text):
            if self.cursor_controller.current_column >= self.columns:
                break # Stop if we hit the end of the line

            self.draw_char_at_cursor(char, "white") # Default color for now
            self.cursor_controller.move_right() # Advance cursor after drawing char

        # After writing, move cursor to the very end of the written text for subsequent operations
        self.cursor_controller.set_position_by_line_col(target_line, len(text))


    def new_line(self) -> None:
        """Moves the cursor to the next line, handling scrolling."""
        if not self.cursor_controller:
            return

        self.cursor_controller.move_to_next_line()
        # If cursor moved to a new line beyond screen, scroll up
        if self.cursor_controller.current_line >= self.lines:
            self._scroll_up()

        self.cursor_controller.move_to_column(0) # Move to the beginning of the new line
        self.update_cursor_position(visible=True)


    def _scroll_up(self) -> None:
        """Simulates scrolling by moving all text up one line and clearing the bottom line."""
        # This method moves all canvas items that represent characters up by one line height.
        # It then clears the now-empty last line.
        for item_id in self.find_all():
            # Exclude the cursor rectangle and status text from scrolling
            if item_id == self.cursor_rect_id or self.gettags(item_id) and "status_text" in self.gettags(item_id):
                continue
            self.move(item_id, 0, -self.char_height) # Move item up

        # Clear the now 'empty' last line of the terminal display
        self.clear_line(self.lines - 1)
        # Adjust all cached line positions in cursor_controller if needed (usually not, as it tracks current_line)


    def clear_line(self, line_num: int) -> None:
        """Clears all characters on a specific line by deleting items with corresponding tags."""
        # Find all items that have a tag like "char_<line_num>_*"
        for col in range(self.columns):
            tag = f"char_{line_num}_{col}"
            self.delete(tag) # Delete items with this specific tag

    def clear_all(self) -> None:
        """Clears all text from the terminal canvas."""
        self.delete("all") # Deletes all items on the canvas
        if self.cursor_controller:
            self.cursor_controller.reset_position()
        self.show_status("Terminal cleared.", "green")

    def delete_prompt(self) -> None:
        """Deletes the '>' prompt character at its specific position."""
        # This assumes the prompt is always at column 0 of the current line
        if self.cursor_controller:
            prompt_tag = f"char_{self.cursor_controller.current_line}_0"
            self.delete(prompt_tag)
            # You might need a more specific tag for the prompt if other characters can be at col 0

    def show_status(self, message: str, color: str = "white") -> None:
        """Displays a temporary status message at the bottom of the canvas."""
        # Delete any old status text
        if self.status_label_id:
            self.delete(self.status_label_id)

        status_x = self.canvas_width // 2
        status_y = self.canvas_height - (self.char_height // 2) - 5 # A bit above the bottom edge

        self.status_label_id = self.create_text(
            status_x, status_y,
            text=message,
            font=(self.font[0], self.font[1] - 2), # Slightly smaller font
            fill=color,
            anchor="s", # Anchor to south (bottom-center)
            tags="status_text"
        )
        # Schedule the message to disappear after a few seconds
        self.after(3000, lambda: self.delete("status_text"))