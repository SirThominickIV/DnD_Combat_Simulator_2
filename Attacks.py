import Damage
import SavingThrow

class Attack():

    def __init__(self) -> None:

        self.name = "attack"
        self.basedOnStat = "str"
        self.bonusDamage = 0
        self.proficiency = 0
        self.critRange = 20
        self.savingThrow = SavingThrow.SavingThrow()
        self.damage = [Damage.Damage()]
        



