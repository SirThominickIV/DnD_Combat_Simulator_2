import time
import os
import operator
import copy
import random

from consolemenu import *
from consolemenu.items import *
from consolemenu.format import *
from consolemenu.menu_component import Dimension 

import Creature
import OutputManager

clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')
clearConsole()

###########################################################################################################################################
############################################################# Dungeon Master ##############################################################
###########################################################################################################################################

class DungeonMaster():
    """
    The dungeon master controls each and every battle. It holds on to a lot of important info such as creature lists, winners, losers, etc.
    
    createFreshCreature(): Creates a creature from a path and puts it on a given team.
    resetCreatures(): Resets the HP, initiative, and initiative list of each creature.
    formatTeams(): Sorts the teams based on which ones are alive, which teams they are on, etc.
    removeCreature(): Used for killing a creature. The creature object still exists, it's just forgotten from the turn order and other similar tracking.
    battle(): The big function of the DM. Battle will run a battle 
    """

    def __init__(self) -> None:
        

        # Get all of the creature paths out of the creature directory
        self.fileList = []
        for root, dirs, files in os.walk("creatures/"):
            for file in files:
                #append the file name to the list
                self.fileList.append(os.path.join(root,file))
        self.readablePaths = []
        for s in self.fileList:
            s = s.replace("creatures/","")
            s = s.replace(".json","")
            s = s.replace("_"," ")
            self.readablePaths.append(s)

        # Creature lists, to more easily find a particular creature
        self.freshCreatures = []         # A list of every creature to copy from when doing new battles
        self.initiativeList = []         # This is the turn order, it goes from high to low, then repeats. Only alive creatures are on here.
        self.teamList = [[]]             # This keeps track of which creature is on which team. Only alive creatures are on here.
        self.losers = []                 # Any creature that has died goes here

        # Display dictionary
        self.creatureDisplayDict = [{"name": "", "diedOnRound": 0, "team": "team", "quantity": 0, "objects": []}]

        # General Tracking
        self.winningTeam = -1
        self.teamWinCount = []
        self.simulationActive = False

        # Misc
        
        self.outputManager = OutputManager.OutputManager()



    def createFreshCreature(self, path, team):

        try:
            
            # Create the creature
            newCreature = Creature.Creature().loadFromFile(path)
            newCreature.team = team
            newCreature.teamIndex = team
            newCreature.outputManager = self.outputManager

            return(newCreature)

        except:
            print("!!! WARNING !!! - Something went wrong with adding those creatures. A default creature was created instead.")
            return Creature.Creature()



    def resetCreatures(self):

        # Reset vars
        self.initiativeList = []
        self.teamList = [[]]
        self.losers = []
        self.winningTeam = -1

        # Create the new creatures
        for creature in self.freshCreatures:
            newCreature = copy.copy(creature)               # Copy from the clean copy
            newCreature.resetTempVars(creature.team)        # Set their health and re-roll initiative
            self.initiativeList.append(newCreature)         # Add it to the danger zone

        # Sort the initiative
        self.initiativeList.sort(key=operator.attrgetter("initiativeRoll"))
        self.initiativeList.reverse()   
        
        self.formatTeams()



    def formatTeams(self):

        self.teamList = [[]]

        # Put all creatures into one list
        activeCreatures = []
        for creature in self.initiativeList:
            activeCreatures.append(creature)
        for creature in self.losers:
            activeCreatures.append(creature)

        # For all dead and alive creatures, create a list where they are grouped with their teammates
        for creature in activeCreatures:
            
            creatureAdded = False
            while creatureAdded == False:

                try:
                    # Try to add the creature
                    self.teamList[creature.team].append(creature)    
                    creatureAdded = True

                except:
                    # Creature wasn't added successfully, increase the size of TeamList to fix it
                    self.teamList.append([])   

        # If the last team is empty during a simulation, remove it, but not if there is only 1 team
        if not self.teamList[len(self.teamList)-1] and not self.teamList and self.simulationActive:
            self.teamList.pop(len(self.teamList)-1)

        # Add each creature to the display list/dict to get a quantity of each
        self.creatureDisplayDict = []    
        for creature in activeCreatures: 

            match = False

            for dict in self.creatureDisplayDict:

                if dict["name"] == creature.name and \
                    dict["diedOnRound"] == creature.diedOnRound and \
                    dict["team"] == creature.team:

                    dict["quantity"] += 1
                    dict["objects"].append(creature)
                    match = True

            if not match:
                self.creatureDisplayDict.append({"name": creature.name, \
                                            "diedOnRound": creature.diedOnRound, \
                                            "team": creature.team, 
                                            "quantity": 1, \
                                            "objects":[creature]})

        # Sort the display list
        self.creatureDisplayDict = sorted(self.creatureDisplayDict, key=operator.itemgetter('diedOnRound','quantity', 'team'))

        # If the team list is empty after all of this, then fix that
        if not self.teamList:
            self.teamList = [[]]

        # Reset win counts
        for dict in self.creatureDisplayDict:
            while len(self.teamWinCount) < dict["team"] + 1:
                self.teamWinCount.append(0)



    def removeCreature(self, creature):

        # Add creature to losers list:
        self.losers.append(creature)

        # Initiative List
        index = self.initiativeList.index(creature)
        self.initiativeList.pop(index)

        # Team list
        teamIndex = creature.teamIndex
        innerIndex = self.teamList[teamIndex].index(creature)
        self.teamList[teamIndex].pop(innerIndex)

        # Check to see if that was the last creature on that team:
        if len(self.teamList[creature.teamIndex]) == 0:   

            startIndex = int(creature.teamIndex)

            # Fix the team index of remaining creatures
            for remainingCreature in self.initiativeList:
                if remainingCreature.teamIndex > startIndex:
                    remainingCreature.teamIndex -= 1

            # Remove that team from the list 
            self.teamList.pop(creature.teamIndex)



    def battle(self):

        self.simulationActive = True

        self.resetCreatures()  

        # Check to make sure there is at least 2 creatures
        if len(self.initiativeList) < 1:
            print("\n!!! WARNING !!! - Could not run battle. There needs to be more than 1 creature in the initiative list.")
            return

        # Check to make sure there is at least 2 teams
        if len(self.teamList) <= 1:
            print("\n!!! WARNING !!! - Could not run battle. There needs to be more than 1 team.")
            return


        # FIGHT FIGHT FIGHT!    
        self.winningTeam = -1
        for i in range(1, 10000): #Failsafe for if loop never breaks. Hopefully no battle goes on for more than 10000 turns (16 hours in game!)
            
            # Check for a winning team
            if self.winningTeam >= 0:
                break

            # Output for better viewing of logs
            self.outputManager.addLine(f"====================================================================================================", 0)
            self.outputManager.addLine(f"============================================= Round {i} ==============================================", 0)
            self.outputManager.addLine(f"====================================================================================================", 0)

            # Go down the initiative list, giving each creature a turn
            for creature in self.initiativeList:

                # Check for a winning team
                if self.winningTeam >= 0:
                    break

                # Give the turn
                self.outputManager.addLine("\n", 0)
                effectedCreatures = None
                effectedCreatures = creature.turn(self.teamList)  #Creature.turn returns the creatures that was effected during the turn

                # Quick check against garbage
                if effectedCreatures == None:
                    self.outputManager.addLine(f"!!! WARNING !!! - No creatures were targeted on this turn.", 2)
                    return


                for effectedCreature in effectedCreatures:
                    # Check for a death
                    if effectedCreature.hitPoints > 0:
                        continue

                    # The effected creature died, mark it as dead
                    self.removeCreature(effectedCreature)
                    effectedCreature.diedOnRound = i
                    self.outputManager.addLine(f"\t{effectedCreature.name} died!", 0)
                        
                    # Check to see if the game is finished (1 team remaining)
                    if len(self.teamList) == 1:
                        self.winningTeam = creature.team
                        break

            self.outputManager.addLine("\n", 0)

        # Add to the count of how many times that team X has won
        # Expand list size if needed
        for dict in self.creatureDisplayDict:
            while len(self.teamWinCount) < self.winningTeam + 1:
                self.teamWinCount.append(0)
        self.teamWinCount[self.winningTeam] += 1



        self.outputManager.addLine(f"====================================================================================================", 0)
        self.outputManager.addLine("\n", 0)

        self.formatTeams()
        displayTeams(0)
        self.simulationActive = False
    

DM = DungeonMaster()




###########################################################################################################################################
############################################################# Menu Functions ##############################################################
###########################################################################################################################################



def displayTeam(teamindex, mode):

    global DM

    # Check if it is an empty team, if so, say so
    for i, team in enumerate(DM.teamList):
        if not len(team) and i == teamindex:
            DM.outputManager.addLine("\t\tEmpty", mode)
            return

    # Find the maximum quantity to display (important for displaying 1,000 wolves vs acerak at 129 hp)
    maxQuantity = 0
    for dict in DM.creatureDisplayDict:
        if dict['quantity'] > maxQuantity:
            maxQuantity = dict['quantity']

    # Sort the display list
    DM.creatureDisplayDict = sorted(DM.creatureDisplayDict, key=operator.itemgetter('diedOnRound','quantity', 'team'))

    # Display winning team
    if DM.winningTeam >= 0 and teamindex == DM.winningTeam:

        # Display Dead Creatures
        for dict in DM.creatureDisplayDict:
            if dict["team"] == teamindex and dict["diedOnRound"] > 0:
                DM.outputManager.addLine(f"\t\t{dict['name']} x{dict['quantity']} - Died on round {dict['diedOnRound']}", mode)

        # Display Alive Creatures
        for dict in DM.creatureDisplayDict:
            if dict["team"] == teamindex and dict["diedOnRound"] == 0:
                dict['objects'].sort(key=operator.attrgetter("hitPoints"))

                if dict['quantity'] > 10:
                    # Display by quantity
                    DM.outputManager.addLine(f"\t\t{dict['name']} x{dict['quantity']} - Survived!", mode)
                else:
                    # Display by individual HP
                    for creature in dict['objects']:
                        DM.outputManager.addLine(f"\t\t{creature.name} - {creature.hitPoints} HP", mode)
                    
    # Displaying all creature for when a battle hasn't happened yet
    elif DM.winningTeam == -1:
        for dict in DM.creatureDisplayDict:
            if dict["team"] == teamindex:
                DM.outputManager.addLine(f"\t\t{dict['name']} x{dict['quantity']}", mode)
    
    # Display Dead Creatures - Catch all case
    else:        
        for dict in DM.creatureDisplayDict:
            if dict["team"] == teamindex:
                DM.outputManager.addLine(f"\t\t{dict['name']} x{dict['quantity']} - Died on round {dict['diedOnRound']}", mode)



def displayTeams(mode):

    global DM

    header = "Team"

    # Print the winning team if there is one, and set a header for the rest of the output
    if DM.winningTeam >= 0:
        DM.outputManager.addLine("Winning team:", mode)
        displayTeam(DM.winningTeam, mode)
        DM.outputManager.addLine("Losers: ", mode)
        header = "    Team"

    # Display teams/loser teams
    for t in range(0, len(DM.teamList)):

        # Don't display the winning team, as that was already done
        if t == DM.winningTeam:
            continue

        DM.outputManager.addLine(f"{header} {t+1}:", mode)

        displayTeam(t, mode)



def menu_addCreatures():    
    
    global DM

    # Setup
    DM.resetCreatures()
    DM.formatTeams()
    print("\n")

    # Show the list of available monsters
    print ("[0] Exit to main menu\n")
    for s, i in zip(DM.readablePaths, range(1, len(DM.readablePaths)+1)):
        print(f"[{i}] {s}")
    print ("\n[0] Exit to main menu")
    
    # Get creature input
    i = -1
    while i != 0:
        try:
            i = int(input("\nCreature to add: "))
            creaturePath = DM.fileList[i-1]
            break
        except:
            print("That is not a valid input.")

    # Get creature input
    while i != 0:
        try:
            i = int(input("Quantity: "))
            quantity = i
            break
        except:
            print("That is not a valid input.")

    # Back out of menu if the user typed 0
    if i == 0:
        return

    # Expand the team list if all teams have at least 1 creature
    teamWithEmpty = False
    for team in DM.teamList:
        if not team:
            teamWithEmpty = True
    if not teamWithEmpty:
        DM.teamList.append([])

    # Format current teams, and increase the team size if needed
    print("\n")
    DM.formatTeams()
    if DM.teamList[len(DM.teamList)-1]:
        DM.teamList.append([])

    # Immediately add the creature(s) if there is only 1 team
    if len(DM.teamList) == 1:
        try:
            newCreature = DM.createFreshCreature(creaturePath, 0)
            for i in range(0, quantity):
                DM.freshCreatures.append(copy.copy(newCreature))

        except:
            print("!!! WARNING !!! - Something went wrong with adding those creatures.")
        
        DM.resetCreatures()
        return

    # Show the user what they're doing
    displayTeams(-1)

    # Get team input
    while i != 0:
        try:
            i = int(input(f"\nAdding to team: "))
            if i > len(DM.teamList):
                raise Exception()
            team = i-1
            break
        except:
            print("That is not a valid input.")
    
    # Back out of menu if the user typed 0
    if i == 0:
        return

    # Create the team
    try:
        newCreature = DM.createFreshCreature(creaturePath, team)
        for i in range(0, quantity):
            DM.freshCreatures.append(copy.copy(newCreature))

    except:
        print("!!! WARNING !!! - Something went wrong with adding those creatures.")
    
    DM.resetCreatures()



def menu_clearAll():

    global DM

    DM.freshCreatures = []
    DM.initiativeList = []
    DM.teamList = [[],[]]
    DM.losers = []
    


def menu_runBattle():
    
    global DM

    # Display teams in the overview log
    DM.teamWinCount = []
    DM.formatTeams()
    DM.resetCreatures()
    DM.outputManager.verbose = False
    displayTeams(1)
    DM.outputManager.verbose = True

    # Find out how many battles to run
    battlesToRun = -1
    while battlesToRun < 0:

        print("How many battles should be run?")

        try:
            battlesToRun = int(input("> "))
            DM.outputManager.numBattles = battlesToRun

            # Warn user of excesive simulation time & turn off verbose
            if battlesToRun > 100:
                print("\n")
                input(f"Warning! {battlesToRun} is a lot of battles! You might want to reconsider.\nPress Enter to Continue...")
                DM.outputManager.verbose = False

            if len(DM.initiativeList) > 100:
                print("\n")
                input(f"Warning! {len(DM.initiativeList)} is a lot of creatures! You might want to reconsider.\nPress Enter to Continue...")
                DM.outputManager.verbose = False

        except:
            print("Invalid input. Enter 0 to exit without starting a battle.")


    # Win index logging
    DM.outputManager.winIndexesByTeam = [[]]
    while len(DM.outputManager.winIndexesByTeam) != len(DM.teamList):
        DM.outputManager.winIndexesByTeam.append([])
        

    # Battle for requested ammount
    DM.outputManager.startTime = time.time()

    if not DM.outputManager.verbose:
        print("Running...")

    for i in range(0, battlesToRun):

        print(f"Running Battle {i}")
        DM.outputManager.currentBattle = i
        DM.battle()
        DM.outputManager.winIndexesByTeam[DM.winningTeam].append(i)
        
    DM.outputManager.endTime = time.time()

    # Sort/format the aftermath for display    
    print("")
    DM.formatTeams() 
    DM.outputManager.verbose = False

    # Send the win counts to the output manager
    DM.outputManager.addLine("", 1)
    for i, winCount in enumerate(DM.teamWinCount):
        footer = ""
        if winCount > 0:
            footer = f" - {((winCount/battlesToRun)*100):.2f} % win rate"
        DM.outputManager.addLine(f"Team {i+1} - {winCount} wins{footer}", 1)
    DM.outputManager.addLine("", 1)

    # Save
    DM.outputManager.verbose = True
    DM.outputManager.saveBattles()

    print("\n")
    input("Press Enter to Continue...")
    clearConsole()
        


def menu_displayTeams():

    global DM

    print("\n")
    DM.formatTeams()
    displayTeams(-1)
    print("\n")
    input("Press Enter to Continue...")
    clearConsole()



def menu_addPreset_basic():

    global DM

    DM.freshCreatures.append(DM.createFreshCreature("creatures/Dire_Bear.json", 0))
    DM.freshCreatures.append(DM.createFreshCreature("creatures/Earth_Elemental.json", 1))
    DM.freshCreatures.append(DM.createFreshCreature("creatures/Hill_Giant.json", 2))
    
    DM.resetCreatures()



def menu_addPreset_basic_x10():

    global DM

    c1 = DM.createFreshCreature("creatures/Dire_Bear.json", 0)
    c2 = DM.createFreshCreature("creatures/Earth_Elemental.json", 1)
    c3 = DM.createFreshCreature("creatures/Hill_Giant.json", 2)

    for i in range(0, 10):
        DM.freshCreatures.append(copy.copy(c1))
        DM.freshCreatures.append(copy.copy(c2))
        DM.freshCreatures.append(copy.copy(c3))
    
    DM.resetCreatures()



def menu_addPreset_Random():

    global DM

    teams = random.randint(2, 10)    # Randomly create up to 10 teams
    for t in range(0, teams):

        uniqueCreatures = random.randint(1, 9) # Randomly use up to 9 varieties of creature    
        for i in range(0, uniqueCreatures):

            creatureID = random.randint(0, len(DM.fileList))   # Randomly pick one of the available creatures
            DM.freshCreatures.append(DM.createFreshCreature(DM.fileList[creatureID-1], t)) #Add it
    
    DM.resetCreatures()



def menu_addPreset_KingOfTheHill():

    global DM

    for i, path in enumerate(DM.fileList):
        DM.freshCreatures.append(DM.createFreshCreature(path, i))
    
    DM.resetCreatures()



def menu_addPreset_Commoner():

    global DM

    c = DM.createFreshCreature("creatures/Commoner.json", 0)

    for i in range(0, 10000):
        DM.freshCreatures.append(copy.copy(c))
    
    DM.resetCreatures()



def menu_toggleSaveToFile():

    global DM

    if DM.outputManager.canSaveToFile:
        DM.outputManager.canSaveToFile = False
        print("Saving to file: Disabled")
    else:
        DM.outputManager.canSaveToFile = True
        print("Saving to file: Enabled")

    print("\n")
    input("Press Enter to Continue...")


###########################################################################################################################################
################################################################ Main GUI #################################################################
###########################################################################################################################################



def gui():

    # Create the formatting for the menu
    menu_format = MenuFormatBuilder(max_dimension=Dimension(100,50)) \
        .set_border_style_type(MenuBorderStyleType.HEAVY_BORDER) \
        .set_prompt(">") \
        .set_title_align("center") \
        .set_subtitle_align("center") \
        .set_left_margin(4) \
        .set_right_margin(4) \
        .show_header_bottom_border(True)

    # Create the menus
    main_menu = ConsoleMenu("Dungeons and Dragons Combat Simulator", "Version 2!", formatter=menu_format, clear_screen=True)
    presets = ConsoleMenu("Presets", "Interesting battles to simulate", formatter=menu_format, clear_screen=True)

    # Add functions to preset menu


    preset1 = FunctionItem("Completely Random", menu_addPreset_Random)
    preset2 = FunctionItem("King of the Hill - All creatures in /creatures/ - Free for all", menu_addPreset_KingOfTheHill)
    preset3 = FunctionItem("10,000 peasant", menu_addPreset_Commoner)
    preset4 = FunctionItem("Dire Bear, Earth Golem, Hill Giant x1 Each", menu_addPreset_basic)
    preset5 = FunctionItem("Dire Bear, Earth Golem, Hill Giant x10 Each", menu_addPreset_basic_x10)

    # Adding presets to preset menu
    presets.append_item(preset1)
    presets.append_item(preset2)
    presets.append_item(preset3)
    presets.append_item(preset4)
    presets.append_item(preset5)

    # Building the main menu
    mainItem1 = SubmenuItem("Presets", submenu=presets)
    mainItem2 = FunctionItem("Add Creatures", menu_addCreatures)
    mainItem3 = FunctionItem("Reset Creature List", menu_clearAll)
    mainItem4 = FunctionItem("View Creature List", menu_displayTeams)
    mainItem5 = FunctionItem("Run Battles", menu_runBattle)
    mainItem6 = FunctionItem(f"Toggle Saving to File", menu_toggleSaveToFile)

    # Add the items to the main menu
    main_menu.append_item(mainItem1)
    main_menu.append_item(mainItem2)
    main_menu.append_item(mainItem3)
    main_menu.append_item(mainItem4)
    main_menu.append_item(mainItem5)
    main_menu.append_item(mainItem6)

    main_menu.show()

if __name__ == "__main__":
    gui()

