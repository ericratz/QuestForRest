'''
gamestate.py
Handles the world state
'''

class WorldState:
    def __init__(self):
        self.day = 1
        self.area = "start_screen"
        self.menu_open = False
    
    def getDay(self):
        return self.day
    
    def getArea(self):
        return self.area
    
    def updateDay(self):
        self.day += 1
    
    def updateArea(self, new_area):
        self.area = new_area
        
class PlayerState:
    def __init__(self):
        self.health = 10
        self.gold = 0
    
    def getHealth(self):
        return self.health
    
    def getGold(self):
        return self.gold
    
    def updateHealth(self, new_health):
        if new_health < 0:
            self.health = 0
        else:
            self.health = new_health
        
    def updateGold(self, new_gold):
        self.gold = new_gold