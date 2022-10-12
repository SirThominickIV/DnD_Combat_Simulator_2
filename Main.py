import os
import operator
import copy
import random

from consolemenu import *
from consolemenu.items import *
from consolemenu.format import *
from consolemenu.menu_component import Dimension 

import Creature

# Get all of the creature paths out of the creature directory
fileList = []
for root, dirs, files in os.walk("creatures/"):
	for file in files:
        #append the file name to the list
		fileList.append(os.path.join(root,file))
readablePaths = []
for s in fileList:
    s = s.replace("creatures/","")
    s = s.replace(".json","")
    s = s.replace("_"," ")
    readablePaths.append(s)

# Creature lists, to more easily find a particular creature
freshCreatures = []         # A list of every creature to copy from when doing new battles
initiativeList = []         # This is the turn order, it goes from high to low, then repeats. Only alive creatures are on here.
teamList = [[]]             # This keeps track of which creature is on which team. Only alive creatures are on here.
losers = []                 # Any creature that has died goes here

# Display dictionary
creatureDisplayDict = [{"name": "", "diedOnRound": 0, "team": "team", "quantity": 0, "objects": []}]

# Tracking
winningTeam = -1
simulationActive = False


###########################################################################################################################################
######################################################### Main Program Functions ##########################################################
###########################################################################################################################################



def createFreshCreature(path, team):

    try:
        
        # Create the creature
        newCreature = Creature.Creature().loadFromFile(path)
        newCreature.team = team
        newCreature.teamIndex = team

        return(newCreature)

    except:
        print("!!! WARNING !!! - Something went wrong with adding those creatures. A default creature was created instead.")
        return Creature.Creature()



def resetCreatures():

    global teamList, initiativeList, losers, freshCreatures, winningTeam

    # Reset vars
    initiativeList = []
    teamList = [[]]
    losers = []
    winningTeam = -1

    # Create the new creatures
    for creature in freshCreatures:
        newCreature = copy.copy(creature)           # Copy from the clean copy
        newCreature.resetTempVars(creature.team)    # Set their health and re-roll initiative
        initiativeList.append(newCreature)          # Add it to the danger zone

    # Sort the initiative
    initiativeList.sort(key=operator.attrgetter("initiativeRoll"))
    initiativeList.reverse()   
    
    formatTeams()



def formatTeams():
    # Make a list of the teams
    global teamList, initiativeList, losers, creatureDisplayDict, simulationActive
    teamList = [[]]

    # Put all creatures into one list
    activeCreatures = []
    for creature in initiativeList:
        activeCreatures.append(creature)
    for creature in losers:
        activeCreatures.append(creature)

    # For all dead and alive creatures, create a list where they are grouped with their teammates
    for creature in activeCreatures:
        
        creatureAdded = False
        while creatureAdded == False:

            try:
                # Try to add the creature
                teamList[creature.team].append(creature)    
                creatureAdded = True

            except:
                # Creature wasn't added successfully, increase the size of TeamList to fix it
                teamList.append([])   

    # If the last team is empty during a simulation, remove it, but not if there is only 1 team
    if not teamList[len(teamList)-1] and not teamList and simulationActive:
        teamList.pop(len(teamList)-1)

    # Add each creature to the display list/dict to get a quantity of each
    creatureDisplayDict = []    
    for creature in activeCreatures: 

        match = False

        for dict in creatureDisplayDict:

            if dict["name"] == creature.name and \
                dict["diedOnRound"] == creature.diedOnRound and \
                dict["team"] == creature.team:

                dict["quantity"] += 1
                dict["objects"].append(creature)
                match = True

        if not match:
            creatureDisplayDict.append({"name": creature.name, \
                                        "diedOnRound": creature.diedOnRound, \
                                        "team": creature.team, 
                                        "quantity": 1, \
                                        "objects":[creature]})

    # Sort the display list
    creatureDisplayDict = sorted(creatureDisplayDict, key=operator.itemgetter('diedOnRound','quantity', 'team'))

    # If the team list is empty after all of this, then fix that
    if not teamList:
        teamList = [[]]





def removeCreature(creature):

    global teamList, initiativeList

    # Add creature to losers list:
    losers.append(creature)

    # Initiative List
    index = initiativeList.index(creature)
    initiativeList.pop(index)

    # Team list
    teamIndex = creature.teamIndex
    innerIndex = teamList[teamIndex].index(creature)
    teamList[teamIndex].pop(innerIndex)

    # Check to see if that was the last creature on that team:
    if len(teamList[creature.teamIndex]) == 0:   

        startIndex = int(creature.teamIndex)

        # Fix the team index of remaining creatures
        for remainingCreature in initiativeList:
            if remainingCreature.teamIndex > startIndex:
                remainingCreature.teamIndex -= 1

        # Remove that team from the list 
        teamList.pop(creature.teamIndex)



def battle():

    global winningTeam, simulationActive
    simulationActive = True

    resetCreatures()  

    # Check to make sure there is at least 2 creatures
    if len(initiativeList) < 1:
        print("\n!!! WARNING !!! - Could not run battle. There needs to be more than 1 creature in the initiative list.")
        return

    # Check to make sure there is at least 2 teams
    if len(teamList) <= 1:
        print("\n!!! WARNING !!! - Could not run battle. There needs to be more than 1 team.")
        return


    # FIGHT FIGHT FIGHT!    
    winningTeam = -1
    for i in range(1, 10000): #Failsafe for if loop never breaks. Hopefully no battle goes on for more than 10000 turns (16 hours in game!)

        # Check for a winning team
        if winningTeam >= 0:
            break

        # Go down the initiative list, giving each creature a turn
        for creature in initiativeList:

            # Give the turn
            effectedCreature = creature.turn(teamList)  #Creature.turn returns the creature that was effected during the turn

            # Check for a death
            if effectedCreature.hitPoints > 0:
                continue

            # The effected creature died, mark it as dead
            removeCreature(effectedCreature)
            effectedCreature.diedOnRound = i
            print(f"\n{effectedCreature.name} died!\n")
                
            # Check to see if the game is finished (1 team remaining)
            if len(teamList) == 1:
                winningTeam = creature.team
                break


    # Sort/format the aftermath for display
    formatTeams()
    displayTeams()
    simulationActive = False





###########################################################################################################################################
############################################################# Menu Functions ##############################################################
###########################################################################################################################################


def displayTeam(team):

    global creatureDisplayDict, winningTeam

    # Check if it is an empty team, if so, say so
    if not teamList[team]:
        print("\tEmpty")
        return

    # Find the maximum quantity to display (important for displaying 1,000 wolves vs acerak at 129 hp)
    maxQuantity = 0
    for dict in creatureDisplayDict:
        if dict['quantity'] > maxQuantity:
            maxQuantity = dict['quantity']

    # Sort the display list
    creatureDisplayDict = sorted(creatureDisplayDict, key=operator.itemgetter('diedOnRound','quantity', 'team'))

    if winningTeam >= 0:

        # Display Dead Creatures
        for dict in creatureDisplayDict:
            if dict["team"] == team:
                if dict["diedOnRound"] > 0:
                    print(f"\t{dict['name']} x{dict['quantity']} - Died on round {dict['diedOnRound']}")

        # Display Alive Creatures
        for dict in creatureDisplayDict:
            if dict["team"] == team:
                if dict["diedOnRound"] == 0:
                    dict['objects'].sort(key=operator.attrgetter("hitPoints"))
                    for creature in dict['objects']:
                        print(f"\t{creature.name} - {creature.hitPoints} HP")
    
    else:
        # Display Dead Creatures
        for dict in creatureDisplayDict:
            if dict["team"] == team:
                print(f"\t{dict['name']} x{dict['quantity']}")



def displayTeams():

    global teamList, creatureDisplayDict, winningTeam
    header = "Team"

    # Print the winning team if there is one, and set a header for the rest of the output
    if winningTeam >= 0:
        print("Winning team: ")
        displayTeam(winningTeam)
        print("Losers: ")
        header = "    Team"

    # Display teams/loser teams
    for t in range(0, len(teamList)):

        # Don't display the winning team, as that was already done
        if t == winningTeam:
            continue

        print(f"{header} {t+1}:")

        displayTeam(t)



def menu_addCreatures():
    
    # Setup
    global fileList, teamList
    print("\n")

    # Show the list of available monsters
    print ("[0] Exit to main menu\n")
    for s, i in zip(readablePaths, range(1, len(readablePaths)+1)):
        print(f"[{i}] {s}")
    print ("\n[0] Exit to main menu")
    
    # Get creature input
    i = -1
    while i != 0:
        try:
            i = int(input("\nCreature to add: "))
            creaturePath = fileList[i-1]
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
    for team in teamList:
        if not team:
            teamWithEmpty = True
    if not teamWithEmpty:
        teamList.append([])

    # Format current teams, and increase the team size if needed
    print("\n")
    formatTeams()
    if teamList[len(teamList)-1]:
        teamList.append([])

    # Immediately add the creature(s) if there is only 1 team
    if len(teamList) == 1:
        try:
            newCreature = createFreshCreature(creaturePath, 0)
            for i in range(0, quantity):
                freshCreatures.append(copy.copy(newCreature))

        except:
            print("!!! WARNING !!! - Something went wrong with adding those creatures.")
        
        resetCreatures()
        return

    # Show the user what they're doing
    displayTeams()

    # Get team input
    while i != 0:
        try:
            i = int(input(f"\nAdding to team: "))
            if i > len(teamList):
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
        newCreature = createFreshCreature(creaturePath, team)
        for i in range(0, quantity):
            freshCreatures.append(copy.copy(newCreature))

    except:
        print("!!! WARNING !!! - Something went wrong with adding those creatures.")
    
    resetCreatures()



def menu_clearAll():

    global freshCreatures, initiativeList, teamList, losers

    freshCreatures = []
    initiativeList = []
    teamList = [[],[]]
    losers = []
    


def menu_runBattle():

    battle()

    print("\n")
    input("Press Enter to Continue...")
        


def menu_displayTeams():
    print("\n")
    formatTeams()
    displayTeams()
    print("\n")
    input("Press Enter to Continue...")



def menu_addPreset():

    freshCreatures.append(createFreshCreature("creatures/Dire_Bear.json", 0))
    freshCreatures.append(createFreshCreature("creatures/Earth_Elemental.json", 1))
    freshCreatures.append(createFreshCreature("creatures/Hill_Giant.json", 2))
    
    resetCreatures()

def menu_addPreset_Random():

    teams = random.randint(2, 10)    # Randomly create up to 10 teams
    for t in range(0, teams):

        uniqueCreatures = random.randint(1, 9) # Randomly use up to 9 varieties of creature    
        for i in range(0, uniqueCreatures):

            creatureID = random.randint(0, len(fileList))   # Randomly pick one of the available creatures
            freshCreatures.append(createFreshCreature(fileList[creatureID-1], t)) #Add it
    
    resetCreatures()



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
    main_menu = ConsoleMenu("Dungeons and Dragons Combat Simulator", "Version 2!", formatter=menu_format, clear_screen=False)
    presets = ConsoleMenu("Presets", "Interesting battles to simulate", formatter=menu_format, clear_screen=False)

    # Add functions to preset menu
    preset1 = FunctionItem("Completely Random", menu_addPreset_Random)
    preset2 = FunctionItem("King of the Hill - All creatures in /creatures/ - Free for all", menu_addPreset)
    preset3 = FunctionItem("1,000,000 peasant", menu_addPreset)
    preset4 = FunctionItem("Dire Bear, Earth Golem, Hill Giant x1 Each", menu_addPreset)
    preset5 = FunctionItem("Dire Bear, Earth Golem, Hill Giant x10 Each", menu_addPreset)

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

    # Add the items to the main menu
    main_menu.append_item(mainItem1)
    main_menu.append_item(mainItem2)
    main_menu.append_item(mainItem3)
    main_menu.append_item(mainItem4)
    main_menu.append_item(mainItem5)

    main_menu.show()

gui()

