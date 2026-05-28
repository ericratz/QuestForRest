'''
QuestForRest
Main entry point — initialises state and runs the game loop.
'''

import pygame
pygame.mixer.pre_init(44100, -16, 2, 512)

import data.areas as areas
import state.gamestate as gamestate
import render.display as display
import logic.handlers as handlers
import audio.sounds as sounds

screen = display.init_display()
sounds.init()
sounds.set_sfx_volume(0.5)
sounds.set_music_volume(0.5)
sounds.set_music('village')
pygame.key.set_repeat(250, 60)

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
        dt   = clock.tick(60)
        sounds.tick()
        display.render(screen, wState, pState, area, dt)

    except Exception:
        import traceback
        traceback.print_exc()
        running = False
        pygame.event.pump()

pygame.quit()
