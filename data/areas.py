'''
gameareas.py
Location definitions
'''

class Area:
    def __init__(self, name, text, image, choices):
        self.name    = name
        self.text    = text
        self.image   = image
        self.choices = choices  # dict: key -> (dest, label)


start_screen = Area(
    "start_screen", "", "assets/title.jpg", {}
)

village = Area(
    "village",
    "You are in a quiet village.",
    "assets/inn.jpg",
    {
        "1": ("inn",        "Enter the Inn"),
        "2": ("adventure",  "Embark on Adventure"),
        "3": ("shop",       "Enter the Shop"),
        "4": ("questboard", "View Quest Board"),
    }
)

inn = Area(
    "inn",
    "The inn is warm and welcoming.",
    "assets/inn.jpg",
    {
        "1": ("innkeeper", "Visit the Innkeeper"),
        "2": ("rest",      "Rest Until Morning"),
        "3": ("stash",     "Access Your Stash"),
        "4": ("village",   "Leave Inn"),
    }
)

shop = Area(
    "shop",
    "Welcome to the shop!",
    "assets/inn.jpg",
    {
        "1": ("buy",     "Buy"),
        "2": ("sell",    "Sell"),
        "3": ("village", "Leave"),
    }
)

areas = {
    "start_screen": start_screen,
    "village":      village,
    "inn":          inn,
    "shop":         shop,
}
