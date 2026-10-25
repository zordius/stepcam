"""Key output. Off until toggled on, so a stray run never types into other apps."""


class KeyOutput:
    def __init__(self, enabled=False):
        self.enabled = enabled
        self._kb = None
        self._keys = None
        self._down = set()

    def _init(self):
        # pynput is imported lazily: it needs Accessibility permission on macOS
        from pynput.keyboard import Controller, Key

        self._kb = Controller()
        self._keys = {"up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right}

    def toggle(self):
        if self.enabled:
            self.release_all()  # while still enabled, or send() would drop the releases
        self.enabled = not self.enabled

    def send(self, name, is_down):
        if not self.enabled:
            return
        if self._kb is None:
            self._init()
        if is_down:
            self._kb.press(self._keys[name])
            self._down.add(name)
        else:
            self._kb.release(self._keys[name])
            self._down.discard(name)

    def release_all(self):
        for name in list(self._down):
            self.send(name, False)
