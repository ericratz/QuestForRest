'''
QuestforRest
A rebuild of my untitled c++ text-rpg, now with simple graphics
'''

import pygame
import gameareas
import gamestate
import display

#window and state initialization
screen = display.init_display()
wState = gamestate.WorldState()
pState = gamestate.PlayerState()

#main loop
running = True
while running:
    try:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                #handle exit
                running = False
        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    #toggle menu
                    wState.menu_open = not wState.menu_open
        
                #when menu is closed, handle area choices
                elif not wState.menu_open:
                    area = gameareas.areas[wState.getArea()]
                    if event.unicode in area.choices:
                        next_area = area.choices[event.unicode][0]
                        wState.updateArea(next_area)
    
        #render current area
        area = gameareas.areas[wState.getArea()]
        display.render(screen, wState, area)
    except Exception:
        import traceback
        traceback.print_exc()
        running = False
        pygame.event.pump()
    
pygame.quit()