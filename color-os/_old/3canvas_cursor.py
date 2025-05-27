
# --- 3. CursorState Class (renamed and integrated update_cursor_position) ---
class CursorState:
    """Manages the current cursor position and its movement logic."""
    def __init__(self, char_size: int, start_x: int, start_y: int,
                 canvas_width: int, canvas_height: int) -> None:
        self.char_size = char_size
        self.start_x = start_x
        self.start_y = start_y
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        self.x = start_x
        self.y = start_y

    def get_pos(self) -> Tuple[int, int]:
        """Returns the current cursor (x, y) coordinates."""
        return self.x, self.y

    def set_pos(self, x: int, y: int) -> None:
        """Sets the cursor to a specific position."""
        self.x = x
        self.y = y

    def advance(self) -> Tuple[bool, bool]:
        """Advances cursor for next character. Returns (did_wrap, did_scroll)."""
        did_wrap = False
        did_scroll = False

        self.x += self.char_size
        if self.x >= self.canvas_width - self.char_size + self.start_x:
            self.x = self.start_x
            self.y += self.char_size
            did_wrap = True

        if self.y >= self.canvas_height - self.char_size + self.start_y:
            self.y -= self.char_size # Keep cursor visually on screen after scroll
            did_scroll = True
        return did_wrap, did_scroll

    def move_by(self, delta_x: int, delta_y: int) -> Tuple[bool, bool]:
        """Moves cursor by delta_x and delta_y. Returns (did_wrap, did_scroll)."""
        new_x = self.x + delta_x
        new_y = self.y + delta_y
        did_scroll = False

        # Apply X boundary checks
        if new_x < self.start_x:
            if self.y > self.start_y: # Wrap to end of previous line
                new_x = self.canvas_width - self.char_size # Approx end
                new_y = self.y - self.char_size
            else: # Already on first line, just clamp to start_x
                new_x = self.start_x
        elif new_x >= self.canvas_width - self.char_size + self.start_x:
             new_x = self.canvas_width - self.char_size # Clamp to end of line


        # Apply Y boundary checks (and check for scrolling)
        if new_y < self.start_y:
            new_y = self.start_y # Clamp to top

        elif new_y >= self.canvas_height - self.char_size + self.start_y:
            # If moving down past canvas height, signal for scroll
            did_scroll = True
            # new_y itself won't change; we'll visually scroll the canvas under it.

        self.x = new_x
        self.y = new_y
        return False, did_scroll # Simplified return for move_by for now (no wrap on arbitrary move)

    def reset(self) -> None:
        """Resets cursor to initial position."""
        self.x = self.start_x
        self.y = self.start_y