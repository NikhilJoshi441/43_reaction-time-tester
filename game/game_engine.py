import pygame
from .round import Round

# Game Engine

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (90, 90, 90)
GREEN = (40, 180, 90)
BLUE = (50, 90, 170)

class GameEngine:
    def __init__(self, width, height, rounds_total=5, min_wait_ms=1000, max_wait_ms=3000):
        if rounds_total < 1:
            raise ValueError("rounds_total must be at least 1")

        self.width = width
        self.height = height

        self.rounds_total = rounds_total
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

        self.round = Round(self.min_wait_ms, self.max_wait_ms)
        self.reaction_times = []
        self.rounds_completed = 0

        self.result_shown_at = None
        self.result_pause_ms = 800  # brief pause on the result screen between rounds
        self._last_round_state = self.round.state
        self._game_over_logged = False

        self.font = pygame.font.SysFont("Arial", 30)
        self.big_font = pygame.font.SysFont("Arial", 46)
        self.game_over = False
        self.exit_requested = False
        self._sounds = self._create_sounds()

    @staticmethod
    def _create_sounds():
        """Create short feedback tones when the platform mixer is available."""
        if pygame.mixer.get_init() is None:
            return {}

        try:
            import array
            import math

            sample_rate = 44100

            def tone(frequency, duration_ms):
                samples = int(sample_rate * duration_ms / 1000)
                data = array.array(
                    "h",
                    (
                        int(32767 * 0.25 * math.sin(2 * math.pi * frequency * i / sample_rate))
                        for i in range(samples)
                    ),
                )
                return pygame.mixer.Sound(buffer=data.tobytes())

            return {
                "go": tone(880, 100),
                "false_start": tone(220, 180),
                "complete": tone(660, 250),
            }
        except pygame.error:
            return {}

    def _play_sound(self, name):
        sound = self._sounds.get(name)
        if sound is not None:
            sound.play()

    def handle_event(self, event):
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.start_new_game(rounds_total=5, min_wait_ms=700, max_wait_ms=1800)
                elif event.key == pygame.K_2:
                    self.start_new_game(rounds_total=5, min_wait_ms=1000, max_wait_ms=3000)
                elif event.key == pygame.K_3:
                    self.start_new_game(rounds_total=7, min_wait_ms=1500, max_wait_ms=4000)
                elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.exit_requested = True
            return

        is_click = event.type == pygame.MOUSEBUTTONDOWN
        is_space = event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
        if (is_click or is_space) and self.round.state != "result":
            reaction_ms = self.round.register_input()
            if reaction_ms is None:
                self._play_sound("false_start")
            else:
                self.reaction_times.append(reaction_ms)
            self.result_shown_at = pygame.time.get_ticks()

    def handle_input(self):
        # Reserved for continuously-held-key input; every action here
        # is a discrete click/keypress, handled in handle_event.
        pass

    def update(self):
        if self.game_over:
            return

        self.round.update()
        if self._last_round_state != "go" and self.round.state == "go":
            self._play_sound("go")
        self._last_round_state = self.round.state

        if self.round.state == "result":
            now = pygame.time.get_ticks()
            if self.result_shown_at is not None and now - self.result_shown_at >= self.result_pause_ms:
                self._start_next_round()

    def _start_next_round(self):
        self.rounds_completed += 1
        if self.rounds_completed >= self.rounds_total:
            self.game_over = True
            self._play_sound("complete")
            return
        self.round = Round(self.min_wait_ms, self.max_wait_ms)
        self._last_round_state = self.round.state

    def start_new_game(self, rounds_total=None, min_wait_ms=None, max_wait_ms=None):
        """Reset the session using the supplied settings or the current settings."""
        if rounds_total is not None:
            if rounds_total < 1:
                raise ValueError("rounds_total must be at least 1")
            self.rounds_total = rounds_total
        if min_wait_ms is not None:
            self.min_wait_ms = min_wait_ms
        if max_wait_ms is not None:
            self.max_wait_ms = max_wait_ms

        self.round = Round(self.min_wait_ms, self.max_wait_ms)
        self.reaction_times = []
        self.rounds_completed = 0
        self.result_shown_at = None
        self.game_over = False
        self.exit_requested = False
        self._last_round_state = self.round.state
        self._game_over_logged = False

    def average_reaction_ms(self):
        if not self.reaction_times:
            return 0
        return round(sum(self.reaction_times) / len(self.reaction_times))

    def render(self, screen):
        if self.game_over:
            self._render_game_over(screen)
            return

        if self.round.state == "waiting":
            bg = GRAY
            message = "Wait for green..."
        elif self.round.state == "go":
            bg = GREEN
            message = "Click now!"
        else:
            bg = BLUE
            message = "False start!" if self.round.false_start else f"{self.round.reaction_ms} ms"

        screen.fill(bg)

        text_surf = self.big_font.render(message, True, WHITE)
        text_rect = text_surf.get_rect(center=(self.width // 2, self.height // 2))
        screen.blit(text_surf, text_rect)

        round_num = min(self.rounds_completed + 1, self.rounds_total)
        round_text = self.font.render(f"Round {round_num}/{self.rounds_total}", True, WHITE)
        screen.blit(round_text, (10, 10))

        avg_text = self.font.render(f"Avg: {self.average_reaction_ms()} ms", True, WHITE)
        screen.blit(avg_text, (self.width - 190, 10))

        if self.game_over and not self._game_over_logged:
            print("Session complete! Reaction times (ms):", self.reaction_times)
            print("Average:", self.average_reaction_ms(), "ms")
            self._game_over_logged = True

    def _render_game_over(self, screen):
        screen.fill(BLUE)
        title = self.big_font.render("Session complete!", True, WHITE)
        screen.blit(title, title.get_rect(center=(self.width // 2, 45)))

        summary = self.font.render(
            f"Average: {self.average_reaction_ms()} ms", True, WHITE
        )
        screen.blit(summary, summary.get_rect(center=(self.width // 2, 95)))

        times = ", ".join(f"{time} ms" for time in self.reaction_times)
        results = self.font.render(f"Times: {times or 'No valid reactions'}", True, WHITE)
        screen.blit(results, results.get_rect(center=(self.width // 2, 145)))

        prompt = self.font.render("1 Easy   2 Medium   3 Hard   Esc/Q Exit", True, WHITE)
        screen.blit(prompt, prompt.get_rect(center=(self.width // 2, self.height - 40)))
