import os
import time
import threading

class OutputManager():

    def __init__(self) -> None:

        self.canSaveToFile = False

        self.numBattles = 0

        self.startTime = 0
        self.endTime = 1
        self.ellapsedTime = 1

        self.path = ""

        self.logs = [[]]
        self.overview = []
        self.winIndexesByTeam = [[]]

        self.currentBattle = 0
        self.verbose = True

    def save(self, path, list):

        # Make the directory
        try:
            os.makedirs(self.path)
        except:
            pass

        with open(f"{self.path}{path}", "w") as txt_file:
            for line in list:
                txt_file.write(f"{line}\n")


    # The main save function, call this at the end of battle(s)
    def saveBattles(self):     

        date = time.ctime()
        date = date.replace(" ", "_")
        date = date.replace(":", "_")   

        self.path = f"Results\\{date}"  

        # Add the win indexes if there was more than one battle
        self.verbose = False
        if self.numBattles > 1:        
            self.overview.append("")
            self.overview.append("Wins by battle number:")
            for i, winIndexes in enumerate(self.winIndexesByTeam):
                self.overview.append(f"Team {i+1}:")
                self.overview.append(f"\t{self.compactRange(winIndexes)}")

        # Add the time stamp
        self.overview.append("")
        self.overview.append(f"Time Started: {time.ctime(self.startTime)}")
        self.overview.append(f"Time Finished: {time.ctime(self.endTime)}")

        timeUsed = self.endTime - self.startTime
        self.ellapsedTime = (time.strftime("%H:%M:%S",time.gmtime(timeUsed)))

        self.overview.append(f"Elapsed Time: {self.ellapsedTime}")
        self.verbose = True

        # Print the overview
        for line in self.overview:
            print(line)



        # Stop here if nothing will be saved
        if not self.canSaveToFile:
            return

        # Save individual battles
        for i, log in enumerate(self.logs):            

            self.save(f"\\Battle_{i}.txt", log)
        self.logs = [[]]      

        # Save the overview
        path = f"\\Overview.txt"        
        self.save(path, self.overview)
        self.overview = []
        
        print("")
        print(f"Overview saved to {self.path}\\Overview.txt")
        print(f"See {self.path} for detailed results.")




    # All logs get added in here
    def addLine(self, line, mode):
        """
        line: The input that will be saved/sent to the console
        mode:   0 - Will only be saved in the log of the battle
                1 - Will be saved only in the overview
                2 - Will be saved in both - For warnings & such
        """

        if self.verbose or mode == 2:
            print(line)

        with threading.Lock():
            
            # Individual battle logs
            if mode == 0 or mode == 2:

                # Expand list if needed
                if len(self.logs) == self.currentBattle:
                    self.logs.append([])

                self.logs[self.currentBattle].append(line)
            
            # Overview and warnings
            if mode == 1 or mode == 2:
                self.overview.append(line)



    def compactRange(self, range):

        # Garbage prevention
        if not len(range):
            return "No wins"

        # Setup
        range.sort()
        output = ""
        start = range[0]
        last = range[0]

        # Terminator for the end of the range
        range.append(-2) 

        for i in range:

            # If the new number is not adjacent to the old one, we have a completed pair/'island' number
            # And if it is -2, then we hit the end of the list, so add what we have
            if i > last + 1 or i == -2:
                if start == last:
                    output = f"{output}, {last}"
                else:
                    output = f"{output}, {start}-{last}"
                start = i
                
            last = i

        # Remove the ", " before returning
        return output[2:]
