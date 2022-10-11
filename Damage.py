import random

class Damage():


    def __init__(self) -> None:
    
        self.dieSize = 4
        self.numberOfDie = 1
        self.basedOnStat = "str"
        self.bonus = 0
        self.type = "slashing"

    def roll(self):

        damage = 0

        for i in range(0, self.numberOfDie):

            damage += random.randint(1, self.dieSize) + self.bonus

        return damage