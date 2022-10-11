import os
import operator
import copy

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
teamList = [[],[]]          # This keeps track of which creature is on which team. Only alive creatures are on here.
losers = []                 # Any creature that has died goes here

# Display dictionary
creatureDisplayDict = [{}]


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

    global teamList, initiativeList, losers, freshCreatures

    # Reset Lists
    initiativeList = []
    teamList = [[],[]]
    losers = []

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
    global teamList, initiativeList, losers
    teamList = [[]]

    # Put all creatures into one list
    activeCreatures = []
    for creature in initiativeList:
        activeCreatures.append(creature)
    for creature in losers:
        activeCreatures.append(creature)

    # For all dead and alive creatures, create a list where they are grouped with their teammates
    for creature in activeCreatures:
        
        creatureAdded = False           # Track if the creature has been able to be added
        while creatureAdded == False:
            try:
                teamList[creature.team].append(creature)    # Try to add the creature
                creatureAdded = True                        # The creature was successfully added, break this loop
            except:
                teamList.append([])                         # Creature wasn't added successfully, increase the size of TeamList to fix it

    # If the last team is empty, remove it
    if len(teamList[len(teamList)-1]) == 0:
        teamList.pop(len(teamList)-1)



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
        



    # Sort/formatt the aftermath for display
    formatTeams()
    losers.sort(key=operator.attrgetter("team"))
    for team in teamList:
        if team[0].team == winningTeam:
            team.sort(key=operator.attrgetter("hitPoints", "diedOnRound"))      # Sort the winning team by the round it died, then HP
        else:
            team.sort(key=operator.attrgetter("diedOnRound"))                   # Sort losing teams by the turn they died on

    # Display winners
    print("Winning team: ")
    for team in teamList:
        if team[0].team == winningTeam:
            for creature in team:
                if creature.hitPoints > 0:
                    print(f"\t{creature.name} - {creature.hitPoints} HP")
                else:
                    print(f"\t{creature.name} - Died on round {creature.diedOnRound}")
    
    # Display losers
    print("\nLosers: ")
    for team in teamList:
        if team[0].team != winningTeam:
            print(f"    Team {team[0].team + 1}:")
            for creature in team:
                print(f"\t{creature.name} - Died on round {creature.diedOnRound}")





###########################################################################################################################################
############################################################# Menu Functions ##############################################################
###########################################################################################################################################



def displayTeams():

    global teamList

    for team, i in zip(teamList, range(0, len(teamList))):
        print(f"Team {i+1}:")
        if len(team) > 0:            
            for creature in team:
                print(f"\t{creature.name}")
        else:
            print("\tEmpty team")



def menu_addCreatures():
    
    # Setup
    formatTeams()
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
        if len(team) == 0:
            teamWithEmpty = True
    if not teamWithEmpty:
        teamList.append([])

    # Show the current team list
    print("\n")
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
    displayTeams()
    print("\n")
    input("Press Enter to Continue...")



def menu_addPreset():

    freshCreatures.append(createFreshCreature("creatures/Dire_Bear.json", 0))
    freshCreatures.append(createFreshCreature("creatures/Earth_Elemental.json", 1))
    freshCreatures.append(createFreshCreature("creatures/Hill_Giant.json", 2))
    
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
    preset1 = FunctionItem("Completely Random", menu_addPreset)
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

