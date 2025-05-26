import pygame

class GameTimer:
    def __init__(self):
        self.start_ticks = None
        self.paused_ticks = 0
        self.pause_start_ticks = None
        self.is_running = False
        self.is_paused = False
        self.current_time = 0
        self.final_time = 0
    
    def start(self):
        """Start the timer only if it hasn't been started yet"""
        if not self.is_running:
            self.start_ticks = pygame.time.get_ticks()
            self.is_running = True
    
    def update(self):
        """Update the current time"""
        if self.is_running and not self.is_paused:
            current_ticks = pygame.time.get_ticks()
            self.current_time = (current_ticks - self.start_ticks - self.paused_ticks) / 1000.0
    
    def pause(self):
        """Pause the timer"""
        if self.is_running and not self.is_paused:
            self.pause_start_ticks = pygame.time.get_ticks()
            self.is_paused = True
    
    def resume(self):
        """Resume the timer"""
        if self.is_running and self.is_paused:
            current_ticks = pygame.time.get_ticks()
            self.paused_ticks += current_ticks - self.pause_start_ticks
            self.is_paused = False
    
    def stop(self):
        """Stop the timer and return the final time"""
        if self.is_running:
            self.update()
            self.is_running = False
            self.final_time = self.current_time
            return self.final_time
        return 0
    
    def reset(self):
        """Reset the timer"""
        self.start_ticks = None
        self.paused_ticks = 0
        self.pause_start_ticks = None
        self.is_running = False
        self.is_paused = False
        self.current_time = 0
        self.final_time = 0
        self.has_started = False
    
    def format_time(self, time_value):
        """Format time as MM:SS.ms"""
        minutes = int(time_value // 60)
        seconds = int(time_value % 60)
        milliseconds = int((time_value % 1) * 1000)
        return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    
    def get_display_time(self):
        """Get the current display time (final if stopped, current if running)"""
        return self.final_time if not self.is_running else self.current_time
    
    def get_formatted_time(self):
        """Get the formatted display time"""
        return self.format_time(self.get_display_time())
    