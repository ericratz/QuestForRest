'''
display.py
Handles the window and rendering things onto the screen
'''

import pygame

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

#set up the window
def init_display():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("QuestForRest")
    return screen

#render information on the screen
def render(screen, state, area):
    width, height = screen.get_size()
    #handle font
    font_size = max(int(height * 0.03), 16)  #3% of height, min 16
    font = pygame.font.SysFont("Arial", font_size)
    
    #load background image
    background = pygame.image.load(area.image).convert()
    background = pygame.transform.scale(background, (width, height))
    screen.blit(background, (0, 0))

    '''
    #HUD
    time_text = font.render(f"Day: {state.day}", True, (0, 0, 0))
    screen.blit(time_text, (width - 200, 50))
    '''
    
    #text box size and position
    bar_height = font.get_height() * 3 + 20  #allow for 3 lines of text + some padding
    bar_surface = pygame.Surface((width, bar_height), pygame.SRCALPHA)  # allow and set alpha for semi-transparency
    bar_surface.fill((0, 0, 0, 150))
    screen.blit(bar_surface, (0, height - bar_height)) #bottom of screen
    
    #text line 1
    text_padding = 10
    main_text1 = font.render(area.text, True, (255, 255, 255))
    screen.blit(main_text1, (text_padding, height - bar_height + text_padding))
    
    '''
    #text line 2
    main_text2 = font.render("", True, (255, 255, 255))
    screen.blit(main_text2, (text_padding, height - bar_height + text_padding + font.get_height()))
    '''
    
    #text line 3 - options line
    options_lines = [f"{key}: {desc}" for key, (_, desc) in area.choices.items()]
    options_text = font.render(" | ".join(options_lines), True, (255, 255, 255))
    screen.blit(options_text, (text_padding, height - bar_height + text_padding + font.get_height() * 2))

    #when open, render the menu
    if state.menu_open:
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        menu_text = [
            "Game Menu",
            "1: View Stats",
            "2: Inventory (coming soon)",
            "ESC: Close Menu"
        ]
        y = 50
        for line in menu_text:
            t = font.render(line, True, (255, 255, 255))
            screen.blit(t, (50, y))
            y += font.get_height() + 10

    pygame.display.flip()