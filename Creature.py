import os
import jsonpickle
import random

import Attacks


class Creature():

    # Things that change during battle
    def resetTempVars(self, team = 0, teamList = []):

        # Simulator Variables
        self.teamList = teamList                # This is a list of all creatures, both enemy and ally
        self.team = team                        # The static ID of the team
        self.teamIndex = team                   # The not so static ID of the team (For when teams get removed)
        self.diedOnRound = 0
        self.target = None                      # The creature being targeted by this creature

        # Actual DnD variables
        self.initiativeRoll = random.randint(1, 20) + self.initiative
        self.hitPoints = int(self.maxHitPoints)
        self.tempHitPoints = 0
        self.conditions = None
        self.advantage = { "default": 0}        # This is a special, and neat edge case. Advantage/disadvantage is actually a list of +1s and -1s that get added up in a special way


    def __init__(self) -> None:

        # Overview
        self.name = "creature"
        self.race = ""
        self.PCclass = None             # TODO: Add player classes
        self.challengeRating = 0

        # Stats
        self.stats = {
            "str": 0,
            "dex": 0,
            "con": 0,
            "int": 0,
            "wis": 0,
            "cha": 0
        }
        
        # Saving throws
        self.savingThrows = {
            "str": 0,
            "dex": 0,
            "con": 0,
            "int": 0,
            "wis": 0,
            "cha": 0
        }

        # General battle stats
        self.armorClass = 10
        self.initiative = 0
        self.speed = 30
        self.maxHitPoints = 10

        # Misc static stats
        self.proficiencies = []     # TODO: Add this in. This would soley be for grappling tbh. Should be implemented like SelfDamageMod
        self.expertice = []
        self.classPoints = 0        # For things like # of rages/sorcery points, bardic inspirations, etc

        # SelfDamageMod - A monstrosity (get it?) of immunities, resistences, and vulnerabilities
                                # 0     = Immunity to this damage
                                # 0.5   = Resistence to this damage
                                # 1     = Nothing
                                # 2     = Vulnerability to this damage
        self.SelfDamageMod = {
            "slashing": 1,
            "bludgeoning": 1,
            "piercing": 1,
            "magical_slashing": 1,
            "magical_bludgeoning": 1,
            "magical_piercing": 1,
            "fire": 1,
            "cold": 1,
            "necrotic": 1,
            "radiant": 1,
            "lightning": 1,
            "psychic": 1,
            "thunder": 1,
            "force": 1,
            "poison:": 1,
            "acid": 1
        }

        # ConditionImmunities - The immunities/resistences of all conditions
                            # 1 = Normal
                            # 0 = Immune
        self.ConditionImmunities = {
            "blinded": 1,
            "charmed": 1,
            "deafened": 1,
            "frightened": 1,
            "grappled": 1,
            "incapacitated": 1,
            "invisible": 1,
            "paralyzed": 1,
            "petrified": 1,
            "poisoned": 1,
            "prone": 1,
            "restrained": 1,
            "stunned:": 1,
            "unconscious": 1,
            "exhaustion": 1
        }

        # Things to use in battle
        self.attacks = [Attacks.Attack()]
        self.multiAttack = []

        self.resetTempVars()



    def loadFromFile(self, path):

        # Do a quick path check
        if not os.path.exists(path):
            print(f"\n!!! WARNING !!! - Could not run reach the specified path. Given path: {path}")
            return
        
        # Continue with loading if the path is valid

        # Load the pickle string from the file
        with open(path) as f:
            pickleString = f.read()

        # Load all the attributes into this object
        creature = jsonpickle.decode(pickleString)

        print(f"Creature loaded from {path}")
        creature.resetTempVars()
        return creature

    def saveToFile(self, path = ""):

        # Reset these, as they shouldn't be saved to file
        self.resetTempVars()

        # Set a default path
        if path == "":
            path = f"{self.name}.json"
        path = path.replace(" ", "_")

        # Encode the creature as a .json
        pickleString = jsonpickle.encode(self)

        # Save it to the path
        with open(path, "w") as outfile:
            outfile.write(pickleString)

        print(f"Creature saved as {path}")


    def action(self):
        pass




    def bonusAction(self):
        pass




    def attack(self):

        # Check to see if the creature has attacks
        if not self.attacks:
            print(f"!!! WARNING !!! - {self.name} has no attacks, yet attack() was called.")
            return

        creature = self.getTarget()
        effectedCreatures = []

        def singleAttack(attack):
            
            # Check that a valid target was found
            if creature == 0:
                return

            # Roll to hit the other creature
            roll = random.randint(1, 20) 
            rollBonuses = + self.stats[attack.basedOnStat] + attack.proficiency + attack.bonusDamage
            totalRoll = roll + rollBonuses

            # Determining crit & giving a little output
            crit = False
            if roll >= attack.critRange:
                crit = True
                print(f"{self.name} used {attack.name} and rolled a critical on {creature.name}.")
            else:
                print(f"{self.name} used {attack.name} and rolled a {totalRoll} to hit {creature.name}.")        

            # Check to see if it was a miss
            if totalRoll < creature.armorClass and not crit:
                return

            # Apply each of the damage types
            for damage in attack.damage:

                d = 0

                # Round down    Roll the damage                                                Apply resistences/immunities/vulnerabilities
                #    \/           \/                                                                                  \/
                d += int((damage.roll() + self.stats[attack.basedOnStat] + attack.proficiency) * creature.SelfDamageMod[damage.type])
                #                                 \/                            \/
                #                      Add str/dex/etc                    Add proficiency bonus (if there is one)    

                #Crit damage (Add double the damage dice)
                if crit:
                    d += int(damage.roll() * creature.SelfDamageMod[damage.type])

                # Apply damage
                print(f"\t{creature.name} took {d} {damage.type} damage.")
                creature.hitPoints -= d
                effectedCreatures.append(creature)


        # Multi attack
        if self.multiAttack:                        # If there is a multi attack
            for attackName in self.multiAttack:     # Get all the attack names
                for attack in self.attacks:         # Search each attack
                    if attack.name == attackName:   # If the attack names match, use that attack
                        singleAttack(attack)
                        creature = self.getTarget()
                        break
                        
        
        # If there is no multi attack, just use the first attack TODO: Have creatures decide which one is best
        else:
            singleAttack(self.attacks[0])

        return [*set(effectedCreatures)]

            

    def getTarget(self):

        # Go for the creature that was attacked last round if it is still alive
        if self.target is not None and self.target.hitPoints > 0:
            return self.target

        while True:

            # Find a team to target
            allowedValuesTeam = list(range(0, len(self.teamList)))
            allowedValuesTeam.remove(self.teamIndex)    

            while True:       

                # Check that other teams are alive
                if not len(allowedValuesTeam):
                    return 0     

                # Find a creature within a team to target
                targetedTeamIndex = random.choice(allowedValuesTeam)
                allowedValuesCreature = list(range(0, (len(self.teamList[targetedTeamIndex]))))

                while True:

                    # Check that there are creatures left on the team
                    if not len(allowedValuesCreature): 
                        allowedValuesTeam.remove(targetedTeamIndex)
                        break 

                    # Choose a creature
                    targetedCreatureIndex = random.choice(allowedValuesCreature)
                    targetedCreature = self.teamList[targetedTeamIndex][targetedCreatureIndex]

                    # Check that it is a valid target
                    if targetedCreature.hitPoints <= 0:
                        allowedValuesCreature.remove(targetedCreatureIndex)
                        continue

                    # Target is valid
                    self.target = targetedCreature
                    return targetedCreature



    # This is the main function within creature. Call this to give a creature a turn. From there the
    # creature will do it's own thing.
    def turn(self, teamList):     

        # Update the team list:
        self.teamList = teamList   

        # Attack that creature
        return self.attack()


