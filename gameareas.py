'''
areas.py
A class of locations, decisions, and text
'''
class Area:
    def __init__(self, name, text, image, choices):
        self.name = name
        self.text = text
        self.image = image
        self.choices = choices

start_screen = Area(
    "start_screen",
    "",
    "assets/title.jpg",
    {}
    )

village = Area(
    "village",
    "You are in a village.",
    "assets/inn.jpg",
    {"1": ("forest", "Go to the forest"),
     "2": ("shop",   "Enter the shop")}
    )

shop = Area(
    "shop",
    "Welcome to the shop!",
    "assets/inn.jpg",
    {"1": ("buy",     "Buy"),
     "2": ("sell",    "Sell"),
     "3": ("village", "Leave")}
    )

forest = Area(
    "forest",
    "You have entered the dark forest.",
    "assets/forest.jpg",
    {"1": ("village", "Return to village"),
     "2": ("cave",    "Venture deeper")}
    )

cave = Area(
    "cave",
    "A large cave looms in front of you.",
    "assets/cave.jpeg",
    {"1": ("forest", "Head back to the forest"),
     "2": ("cave",   "Enter the cave")}
    )

areas = {
    "start_screen": start_screen,
    "village":      village,
    "shop":         shop,
    "forest":       forest,
    "cave":         cave,
    }
