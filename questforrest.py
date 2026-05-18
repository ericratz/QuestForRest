'''
QuestForRest
Main entry point — initialises state and runs the game loop.
'''

import pygame
import data.areas as areas
import state.gamestate as gamestate
import render.display as display
import logic.handlers as handlers

screen = display.init_display()
clock  = pygame.time.Clock()
wState = gamestate.WorldState()
pState = gamestate.PlayerState()

running = True
while running:
    try:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type != pygame.KEYDOWN:
                continue
            if handlers.handle_event(event.key, event, wState, pState) == "exit":
                running = False

        area = areas.areas[wState.getArea()]
        display.render(screen, wState, pState, area)
        clock.tick(60)

    except Exception:
        import traceback
        traceback.print_exc()
        running = False
        pygame.event.pump()

pygame.quit()
