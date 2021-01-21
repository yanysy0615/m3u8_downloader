class SimpleLock:
    def __init__(self, val=False):
        self.val = val

    def is_locked(self):
        return self.val
    
    def set(self, val):
        self.val = val