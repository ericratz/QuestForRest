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
    "start_screen", "", "assets/images/Title Screen.jpg", {}
)

village = Area(
    "village",
    "You are in a quiet village.",
    "assets/images/Restholm.jpg",
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
    "assets/images/Inn Inside.jpeg",
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
    "assets/images/Restholm.jpg",
    {
        "1": ("buy",                       "Buy"),
        "2": ("sell",                      "Sell"),
        "3": ("talk:restholm_shopkeeper",  "Talk to Mira"),
        "4": ("village",                   "Leave"),
    }
)

duskwall = Area(
    "duskwall",
    "The streets of Duskwall. Older. Quieter. Harder.",
    "assets/images/Duskwall.jpeg",
    {
        "1": ("duskwall_tavern",          "Enter the Tavern"),
        "2": ("duskwall_adventure",       "Embark on Adventure"),
        "3": ("duskwall_shop",            "Enter the Shop"),
        "4": ("innkeeper",                "Visit the Guildmaster"),
        "5": ("talk:duskwall_merchant",   "Talk to the Merchant"),
        "6": ("currency_exchange",        "Currency Exchange"),
        "7": ("questboard",               "View Bounty Board"),
    }
)

duskwall_tavern = Area(
    "duskwall_tavern",
    "The Hollow Crown. Low ceilings, lower expectations.",
    "assets/images/Inn Inside.jpeg",
    {
        "1": ("rest",                  "Rest Until Morning"),
        "2": ("stash",                 "Access Your Stash"),
        "3": ("talk:duskwall_barkeep", "Talk to the Barkeep"),
        "4": ("talk:duskwall_mystic",  "The Mystic"),
        "5": ("duskwall",              "Leave Tavern"),
    }
)

duskwall_shop = Area(
    "duskwall_shop",
    "Sparse shelves. What's here costs more than you'd like.",
    "assets/images/Duskwall.jpeg",
    {
        "1": ("buy",      "Buy"),
        "2": ("sell",     "Sell"),
        "3": ("duskwall", "Leave"),
    }
)

areas = {
    "start_screen":    start_screen,
    "village":         village,
    "inn":             inn,
    "shop":            shop,
    "duskwall":        duskwall,
    "duskwall_tavern": duskwall_tavern,
    "duskwall_shop":   duskwall_shop,
}
