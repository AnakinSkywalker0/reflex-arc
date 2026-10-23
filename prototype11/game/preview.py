"""Save reproducible UI previews without launching a mission or calling a model."""
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import chat
import config as C
import render
import settings as S
from world import World


def main():
    pygame.init()
    S.STORM_ON = False
    output = Path(__file__).resolve().parents[1] / "previews"
    output.mkdir(exist_ok=True)
    try:
        for name, tile, width, revealed in (
            ("reference2-dashboard", 24, 530, True),
            ("reference2-laptop", 16, 530, True),
            ("reference2-fog", 16, 530, False),
        ):
            C.TILE, S.CHAT_W = tile, width
            w = World()
            w.phase = "day"
            if revealed:
                w.here.seen.update((x, y) for y in range(w.here.h)
                                   for x in range(w.here.w))
            conv = chat.Conversation(w)
            conv.lines = [("gemma", "Ready to survey Jezero flats. Set a mission "
                           "objective or send a route instruction.")]
            fonts = render.Fonts()
            game = pygame.Surface(render.game_size())
            pane = pygame.Surface((width, game.get_height()))
            render.draw_world(game, w, fonts)
            render.draw_chat(pane, conv, w, fonts, "", False, 0)
            screen = pygame.Surface(render.window_size())
            screen.blit(game, (0, 0))
            screen.blit(pane, (game.get_width(), 0))
            path = output / f"{name}.png"
            pygame.image.save(screen, path)
            print(path)
            if name == "reference2-dashboard":
                w.notes.remember("Survey plan", "Survey the eastern ridge, then return to the charging pad.")
                w.notes.remember("Next sol", "Revisit unfinished sites after recharging.")
                render.D.memory_fraction = .72
                render.draw_chat(pane, conv, w, fonts, "", False, 0)
                screen.blit(pane, (game.get_width(), 0))
                pygame.image.save(screen, output / "memory-open.png")
                render.D.memory_fraction = 0

                expanded = pygame.Surface((1280, 960))
                render.draw_map(expanded, w, fonts, w.pos)
                path = output / "reference2-map.png"
                pygame.image.save(expanded, path)
                print(path)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
