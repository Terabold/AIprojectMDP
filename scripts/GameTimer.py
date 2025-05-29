import pygame

class GameTimer:
    def __init__(self):
        self.start_ticks = 0
        self.paused_duration = 0
        self.pause_start = 0
        self.is_running = False
        self.is_paused = False
        self._cached_time = 0.0
        self._last_update_tick = 0
    
    def start(self):
        if not self.is_running:
            self.start_ticks = pygame.time.get_ticks()
            self._last_update_tick = self.start_ticks
            self.is_running = True
    
    def update(self):
        if not (self.is_running and not self.is_paused):
            return
        now = pygame.time.get_ticks()
        if now - self._last_update_tick >= 16:
            self._cached_time = (now - self.start_ticks - self.paused_duration) * 0.001
            self._last_update_tick = now

    
    def pause(self):
        if self.is_running and not self.is_paused:
            self.pause_start = pygame.time.get_ticks()
            self.is_paused = True
    
    def resume(self):
        if self.is_running and self.is_paused:
            self.paused_duration += pygame.time.get_ticks() - self.pause_start
            self.is_paused = False
    
    def stop(self):
        if self.is_running:
            self.update()
            self.is_running = False
            return self._cached_time
        return 0.0
    
    def reset(self):
        self.start_ticks = 0
        self.paused_duration = 0
        self.pause_start = 0
        self.is_running = False
        self.is_paused = False
        self._cached_time = 0.0
        self._last_update_tick = 0
    
    def format_time(self, t):
        ms = int(t * 1000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{m:02}:{s:02}.{ms:03}"

    
    def get_display_time(self):
        if not self.is_running:
            return self._cached_time
        self.update()
        return self._cached_time
    
    def get_formatted_time(self):
        return self.format_time(self.get_display_time())