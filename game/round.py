import random
import pygame

class Round:
    def __init__(self, min_wait_ms=1000, max_wait_ms=3000):
        if min_wait_ms < 0 or max_wait_ms < min_wait_ms:
            raise ValueError("wait times must satisfy 0 <= min_wait_ms <= max_wait_ms")

        self.wait_delay_ms = random.randint(min_wait_ms, max_wait_ms)
        self.state = "waiting"  # "waiting" -> "go" -> "result"
        self.start_time = pygame.time.get_ticks()
        self.go_time = None
        self.reaction_ms = None
        self.false_start = False

    def update(self):
        if self.state == "waiting":
            now = pygame.time.get_ticks()
            if now - self.start_time >= self.wait_delay_ms:
                self.state = "go"
                self.go_time = now

    def register_input(self):
        if self.state == "result":
            return None

        now = pygame.time.get_ticks()
        if self.state == "waiting":
            self.false_start = True
            self.state = "result"
            return None

        self.reaction_ms = now - self.go_time
        self.state = "result"
        return self.reaction_ms
