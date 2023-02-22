"""
This file contains the problem definition of the search problem related to a 
routing problem in a maze.

Some of this code was adapted from the Pacman AI projects developed at UC Berkeley
http://ai.berkeley.edu created by John DeNero
(denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
Student side autograding was added by Brad Miller, Nick Hay, and
Pieter Abbeel (pabbeel@cs.berkeley.edu).
"""

import search
import environment as env
import os
import random


class Grid:
    """
    A 2-dimensional array of objects backed by a list of lists.  Data is accessed
    via grid[x][y] where (x,y) are positions on a BlockGrid with x horizontal,
    y vertical and the origin (0,0) in the top left corner.

    """
    def __init__(self, width, height, initialValue=False):
        if initialValue not in [False, True]: raise Exception('Grids can only contain booleans')
        self.CELLS_PER_INT = 30

        self.width = width
        self.height = height
        self.data = [[initialValue for y in range(height)] for x in range(width)]
        
    def __getitem__(self, i):
        return self.data[i]

    def __setitem__(self, key, item):
        self.data[key] = item

class Layout:
    """
    A Layout manages the static information about the maze/game board.
    """

    def __init__(self, layoutText):
        self.width = len(layoutText[0])
        self.height= len(layoutText)
        self.walls = Grid(self.width, self.height, False)
        self.goalPositions = []
        self.capsules = []
        self.agentPositions = []
        self.numGhosts = 0
        self.processLayoutText(layoutText)
        self.layoutText = layoutText
        # self.initializeVisibilityMatrix()

    def isWall(self, pos):
        x, col = pos
        return self.walls[x][col]

    def getRandomLegalPosition(self):
        x = random.choice(range(self.width))
        y = random.choice(range(self.height))
        while self.isWall( (x, y) ):
            x = random.choice(range(self.width))
            y = random.choice(range(self.height))
        return (x,y)

    def __str__(self):
        return "\n".join(self.layoutText)

    def deepCopy(self):
        return Layout(self.layoutText[:])

    def processLayoutText(self, layoutText):
        """
        Coordinates are flipped from the input format to the (x,y) convention here

        The shape of the maze.  Each character
        represents a different type of object.
         % - Wall
         S - Start point
         G - Goal
        Other characters are ignored.
        """
        maxY = self.height - 1
        for y in range(self.height):
            for x in range(self.width):
                layoutChar = layoutText[y][x]
                self.processLayoutChar(x, y, layoutChar)
        self.agentPositions.sort()
        self.agentPositions = [ ( i == 0, pos) for i, pos in self.agentPositions]

    def processLayoutChar(self, x, y, layoutChar):
        if layoutChar == '%':
            self.walls[x][y] = True
        elif layoutChar == 'S':
            self.agentPositions.append( (0, (x, y) ) )
        elif layoutChar == 'G':
            self.goalPositions.append( (x, y) )
            
def getLayout(name, back = 2):
    if name.endswith('.txt'):
        layout = tryToLoad('layouts/' + name)
        if layout == None: layout = tryToLoad(name)
    else:
        layout = tryToLoad('layouts/' + name + '.txt')
        if layout == None: layout = tryToLoad(name + '.txt')
    if layout == None and back >= 0:
        curdir = os.path.abspath('.')
        os.chdir('..')
        layout = getLayout(name, back -1)
        os.chdir(curdir)
    return layout

def tryToLoad(fullname):
    if(not os.path.exists(fullname)): return None
    f = open(fullname)
    try: return Layout([line.strip() for line in f])
    finally: f.close()



class Obstacle(env.Thing):
    """Something that can cause a bump, preventing an agent from
    moving into the same square it's in."""
    pass    
    
class Wall(Obstacle):
    pass

class GoalPoint(env.Thing):
    pass

class SolutionPathPoint(env.Thing):
    pass

class ReachedPoint(env.Thing):
    pass

class MazeEnvironment(env.GraphicEnvironment):
    def __init__(self,mazeLayout, color={}, display=False):
        """Define all the usual XYEnvironment characteristics,
        but initialise a BlockGrid for GUI too."""
        height = mazeLayout.height
        width  = mazeLayout.width
        super().__init__(width=width, height=height,x_start=0,y_start=0,color=color,display=display)
        for y in range(height):
            for x in range(width):
                if mazeLayout.isWall((x,y)):
                    self.add_thing(Wall(),location=[x,y])
        self.add_thing(env.Agent(),location=mazeLayout.agentPositions[0][1])
        if isinstance(mazeLayout.goalPositions, list):
            for goal in mazeLayout.goalPositions:
                self.add_thing(GoalPoint(),location=goal)
        else:
            self.add_thing(GoalPoint(),location=mazeLayout.goalPositions)
        self.add_thing(GoalPoint(),location=goal)


class MazeProblem(search.SearchProblem):
    """ Describes the search problem defined by a maze grid.
    """
    def __init__(self, filename=None, **kwds):
        """ Initializes maze grid search problem from file indicated by 'filename'.
        """
        mazeLayout = getLayout(filename)
        ##
        initial = mazeLayout.agentPositions[0][1]
        goal = mazeLayout.goalPositions
        ##
        super().__init__(initial=initial,goal=goal)
        self.filename = filename
        self.initial = initial
        self.goal = goal
        self.mazeLayout = mazeLayout
        self.n_rows = mazeLayout.height
        self.n_cols = mazeLayout.width
        
        # For display purposes: 
        #    _reached is a dictionary that contains a state as key with value 'True' 
        #           if that state has already been reached by the search algorithm.
        #    _reachedlist is a list that contains a state if that state has 
        #           already been reached by the search algorithm.
        #    _expanded is an integer that counts how many nodes have been expanded 
        #           so far by the search algorithm.
        self._reached, self._reachedlist, self._expanded = {}, [], 0 # intialize the data structures.
        self._reached[self.initial] = True # set initial state as reached
        self._reachedlist.append(self.initial) # set initial state as reached
        
    def setEnvironment(self):
        self.maze = MazeEnvironment(self.mazeLayout,color={'Wall': (0,0,0), 
                                                           'SolutionPathPoint': (200,0,0),
                                                           'ReachedPoint': (130,130,130),
                                                           'Agent': (0,0,255),
                                                           'GoalPoint': (0,200,0)})
        self.maze.grid.lines_on = False
    
    def visualize(self):
        self.maze.reveal()

    def setSearchResults(self,Node):
        for node in Node.path():
            if not self.maze.list_things_at(location=node.state):
                self.maze.add_thing(SolutionPathPoint(),location=node.state)
        for state in self._reachedlist:
            if not self.maze.list_things_at(location=state):
                self.maze.add_thing(ReachedPoint(),location=state)
        
    def actions(self,state):
        """ Given a state, return a list of all applicable actions.
        Parameters
        ----------
        state : tuple, corresponds to the location of original state
        
        Returns
        -------
        actions : list of str, contains all applicable actions
        """
        actions = ['Left', 'Right', 'Up', 'Down'] #why define an array?
       
        ########### ADD YOUR CODE HERE BELOW ####################
        #actions.append("***")
        ##actions.remove/ actions.pop
        
        #Checks if there is a wall around 'player' and removes direstion
        #if there is
        
        
        x,y = state #(1,2)
        if self.mazeLayout.isWall((x,y+1)):
            actions.remove('Up')
        if self.mazeLayout.isWall((x,y-1)):
            actions.remove('Down')
        if self.mazeLayout.isWall((x-1,y)):
            actions.remove('Left')
        if self.mazeLayout.isWall((x+1,y)):
            actions.remove('Right')

#         actions = []
#         ########### ADD YOUR CODE HERE BELOW ####################
#         x,y = state
#         if not self.mazeLayout.isWall((x,y-1)):
#             actions.append('Down')
#         if not self.mazeLayout.isWall((x,y+1)):
#             actions.append('Up')
#         if not self.mazeLayout.isWall((x-1,y)):
#             actions.append('Left')
#         if not self.mazeLayout.isWall((x+1,y)):
#             actions.append('Right')

            
            
            
#         print(state.initial)
#         print("Test")
#         if actions == 'Left':
#             targetloc = (state.location[0]-1,state.location[1])
#         elif action == 'Right':
#             targetloc = (state.location[0]+1,state.location[1])
#         elif action == 'Up':
#             targetloc = (state.location[0],state.location[1]+1)
#         elif action == 'Down':
#             targetloc = (state.location[0],state.location[1]-1)
        

        #########################################################
        return actions
    
    def result(self,state,action):
        """ Given a state and an action, compute the resulting new state based
        on the transition model that is used.
        Parameters
        ----------
        state : tuple, corresponds to the location of original state
        action : str, encodes the action that is chosen.
        
        Returns
        -------
        newstate : tuple, corresponds to the location of new state
        
        Does the actual movement, returns new state after
        """
        ########### ADD YOUR CODE HERE BELOW ####################
        x,y = state 
        if action == 'Up':
            targetloc = (x,y+1)
        elif action == 'Down':
            targetloc = (x,y-1)
        elif action == 'Left':
            targetloc = (x-1,y)
        elif action == 'Right':
            targetloc = (x+1,y)
            
        if self.mazeLayout.isWall(targetloc):
            targetloc = state
        

        return targetloc

#         x,y = state
#         if action =='Up':
#             newstate = (x,y-1)
#         elif action == 'Down':
#             newstate = (x,y+1)
#         elif action == 'Left':
#             newstate = (x-1,y)
#         elif action == 'Right':
#             newstate = (x+1,y)
        
#         if self.mazeLayout.isWall(newstate):
#             newstate = state
            
#         return newstate

        pass
        #########################################################
        
        
                
    def h(self, node):
        """ Returns the Manhattan distance to goal node as heuristic value for 
        a given state.
        Parameters
        ----------
        node : Node object of search module
        
        Returns
        -------
        value : float, corresponding to Manhattan distance of state of node to 
                goal state
        """
        ########### ADD YOUR CODE HERE BELOW ####################
        x1,y1 = node.state #"player"
        x2,y2 = self.goal[0] #goal, TA said it should work
        distance = (abs(x1-x2) + abs(y1-y2))
        return distance


        pass
        #########################################################
        
