import Creature

# Old stuff used for saving creatures to file TODO: Make some sort of menu based creature builder

c1 = "creatures/Hill_Giant.json"
c2 = "creatures/Dire_Bear.json"

# Stat them up
creature1 = Creature.Creature().loadFromFile(c1)
creature2 = Creature.Creature().loadFromFile(c2)

creature1.saveToFile(f"creatures/{creature1.name}.json")
creature2.saveToFile(f"creatures/{creature2.name}.json")