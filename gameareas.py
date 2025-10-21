'''
areas.py
A class of locations, decisions, and text

Format: 
area_name = Area(
    "area_name",
    "loc info",
    "assets/image.jpg",
    {"1": ("area1", "area1 text"),
     "2": ("area2", "area2 text")}
    )

I can add alternate text or choices when I need to make it more dynamic.
'''
class Area:
    def __init__(self, name, text, image, choices):
        self.name = name
        self.text = text
        self.image = image
        self.choices = choices
        
start_screen = Area(
    "start_screen",
    "Enter '1' to start the game!",
    "assets/title.jpg",
    {"1": ("village", "Head to the village")}
    )

village = Area(
    "village",
    "You are in a village.",
    "assets/inn.jpg",
    {"1": ("village", "Stay in the village"),
     "2": ("forest", "Go to the forest")}
    )

forest = Area(
    "forest",
    "You have entered the dark forest.",
    "assets/forest.jpg",
    {"1": ("village", "Return to village"),
     "2": ("cave", "Venture deeper")}
    )

cave = Area(
    "cave",
    "A large cave looms in front of you.",
    "assets/cave.jpeg",
    {"1": ("forest", "Head back to the forest"),
    "2": ("cave", "Enter the cave")}
    )

areas = {
    "start_screen": start_screen,
    "village": village,
    "forest": forest,
    "cave": cave,
    }