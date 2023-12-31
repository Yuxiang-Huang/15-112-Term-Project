from cmu_graphics import *
import map as mapFile
from destination import *
from railSwitchButton import *
import random


class Rail:
    difToDirection = {
        (-1, 0): "top",
        (1, 0): "bottom",
        (0, -1): "left",
        (0, 1): "right",
    }
    directionToDif = {
        "top": (-1, 0),
        "bottom": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }
    directionComplement = {
        "top": "bottom",
        "bottom": "top",
        "left": "right",
        "right": "left",
    }

    def __init__(self, app, indices, directions):
        self.size = app.unitSize
        self.indices = indices
        self.directions = directions
        self.spawnCarDirection = None
        self.cars = []
        self.destinationList = []
        self.pos = mapFile.Map.toWorldPos(self.indices, app)

    def __repr__(self):
        return f"Pos: {self.indices}, Dir: {self.allDirections}"

    def checkSwitchButtonPress(self, app, mouseX, mouseY):
        # check if any of the button can be pressed
        for switchButton in self.switchButtons:
            if switchButton.pressed(mouseX, mouseY):
                # switch direction to that direction if pressed
                self.directions = self.allDirections[switchButton.index]
        app.selectedRail = None

    def onPress(self, app, button):
        # only switchable rails without car can be clicked
        if len(self.allDirections) > 1 and self.cars == []:
            # left click
            if button == 0:
                # switch to next rail
                self.changeDirectionsHelper(1)
            # right click to select rail
            else:
                # can't select rails with only two possible directions
                if len(self.allDirections) > 2:
                    app.selectedRail = self

    def changeDirectionsHelper(self, deltaIndex):
        # switch to next rail
        self.dirIndex += deltaIndex
        self.dirIndex %= len(self.allDirections)
        self.directions = self.allDirections[self.dirIndex]

    # region display
    def createRailSwitchButtons(self):
        self.switchButtons = []
        sizeFactor = 4 / 5

        # three directions case
        if len(self.allDirections) == 3:
            # find the offset
            xOffSet = 0
            yOffset = -app.unitSize
            # first row case
            if self.indices[0] == 0:
                yOffset = app.unitSize

            # first column case
            if self.indices[1] == 0:
                xOffSet = app.unitSize

            # last column case
            if self.indices[1] == len(app.map.rails[0]) - 1:
                xOffSet = -app.unitSize

            # store background info
            self.switchButtonsBackgroundPos = (
                self.pos[0] + xOffSet,
                self.pos[1] + yOffset + app.unitSize / 2,
            )

            # create one button for each direction
            for i in range(len(self.allDirections)):
                type, angle = self.getTypeAngleForDisplay(self.allDirections[i])
                xCoord = self.pos[0] + (i - 1) * self.size + xOffSet
                yCoord = self.pos[1] + yOffset
                self.switchButtons.append(
                    RailSwitchButton(
                        [xCoord, yCoord], self.size * sizeFactor, type, angle, i
                    )
                )

        # six directions case
        elif len(self.allDirections) == 6:
            # find the offset
            xOffSet = 0
            yOffset = -app.unitSize

            # no other edge cases since it requires six directions

            # second row case
            if self.indices[0] == 1:
                yOffset = app.unitSize * 2

            # store background info
            self.switchButtonsBackgroundPos = (
                self.pos[0] + xOffSet,
                self.pos[1] + yOffset + app.unitSize / 2,
            )

            # create one button for each direction
            for i in range(len(self.allDirections)):
                type, angle = self.getTypeAngleForDisplay(self.allDirections[i])
                xCoord = self.pos[0] + (i % 3 - 1) * self.size + xOffSet

                if self.indices[0] == 1:
                    yCoord = self.pos[1] + yOffset - app.unitSize * (1 - i // 3)
                else:
                    yCoord = self.pos[1] + yOffset + app.unitSize * (i // 3 - 1)

                self.switchButtons.append(
                    RailSwitchButton(
                        [xCoord, yCoord], self.size * sizeFactor, type, angle, i
                    )
                )

    def display(self, app):
        # visualize for multi rail
        if len(self.allDirections) > 1:
            # draw circle background
            drawOval(
                self.pos[0],
                self.pos[1],
                self.size,
                self.size,
                fill="lightyellow",
            )
            # display next rail if app.switch visualizer is on
            if app.switchVisualizer:
                self.changeDirectionsHelper(1)
                type, angle = self.getTypeAngleForDisplay(self.directions)
                drawImage(
                    app.imageDict[type],
                    self.pos[0],
                    self.pos[1],
                    width=self.size,
                    height=self.size,
                    align="center",
                    rotateAngle=angle,
                    opacity=25,
                )
                self.changeDirectionsHelper(-1)
        type, angle = self.getTypeAngleForDisplay(self.directions)
        drawImage(
            app.imageDict[type],
            self.pos[0],
            self.pos[1],
            width=self.size,
            height=self.size,
            align="center",
            rotateAngle=angle,
        )

    def getTypeAngleForDisplay(self, directions):
        # determine rail display dependo on connections
        if "top" in directions and "bottom" in directions:
            type = "Straight"
            angle = 0
        elif "left" in directions and "right" in directions:
            type = "Straight"
            angle = 90
        elif "top" in directions and "left" in directions:
            type = "Turn"
            angle = 90
        elif "top" in directions and "right" in directions:
            type = "Turn"
            angle = 180
        elif "bottom" in directions and "left" in directions:
            type = "Turn"
            angle = 0
        elif "bottom" in directions and "right" in directions:
            type = "Turn"
            angle = 270

        return type, angle

    def selectedRailDisplay(self, app):
        # draw background
        if len(self.allDirections) == 3:
            drawRect(
                self.switchButtonsBackgroundPos[0],
                self.switchButtonsBackgroundPos[1],
                app.unitSize * 3,
                app.unitSize,
                align="bottom",
            )
        elif len(self.allDirections) == 6:
            drawRect(
                self.switchButtonsBackgroundPos[0],
                self.switchButtonsBackgroundPos[1],
                app.unitSize * 3,
                app.unitSize * 2,
                align="bottom",
            )

        # draw rails
        for switchButton in self.switchButtons:
            switchButton.display(app)

    # endregion

    # region rail generation
    def floodFill(self, app, prevDirection):
        # bias to move straight
        if random.random() < app.probOfStraight:
            dif = Rail.directionToDif[prevDirection]
            self.connect(app, dif)

        # try all directions in random order
        choices = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(choices)
        for dif in choices:
            self.connect(app, dif)

    def connect(self, app, dif):
        row = self.indices[0] + dif[0]
        col = self.indices[1] + dif[1]

        # out of bound cases
        if not mapFile.Map.inBound(app.map, (row, col)):
            return

        # if never visited
        if app.map.rails[row][col] == None:
            # create new rail
            app.map.rails[row][col] = Rail(app, (row, col), set())
            # connect to this rail to ensure that all rails are connected
            self.connectToRail(app.map.rails[row][col], dif)
            # flood fill the rest of the map
            app.map.rails[row][col].floodFill(app, Rail.difToDirection[dif])

        # determine using probability of extra connection if to connect to this rail)
        if random.random() < app.probOfExtraConnect:
            self.connectToRail(app.map.rails[row][col], dif)

    def connectToRail(self, other, dif):
        # connect the two rails together using dif
        self.directions.add(Rail.difToDirection[dif])
        other.directions.add(Rail.directionComplement[Rail.difToDirection[dif]])

    def fixOneDirectionRail(self, app, spawnableRails):
        # connect to complement if only has one direction
        if len(self.directions) == 1:
            dif = Rail.directionToDif[Rail.directionComplement[min(self.directions)]]
            otherIndices = (self.indices[0] + dif[0], self.indices[1] + dif[1])
            # in bound and out of bound cases
            if mapFile.Map.inBound(app.map, otherIndices):
                other = app.map.rails[otherIndices[0]][otherIndices[1]]
                self.connectToRail(other, dif)
            else:
                self.outOfBoundConnection(
                    self.indices[0] + dif[0], self.indices[1] + dif[1], spawnableRails
                )

    def connectMultiRail(self, app):
        # connect to the other rail if both are multi rails
        if len(self.directions) > 2:
            # try left and down rails
            for dif in [(0, 1), (1, 0)]:
                otherIndices = (self.indices[0] + dif[0], self.indices[1] + dif[1])
                # need to be inbound
                if mapFile.Map.inBound(app.map, otherIndices):
                    other = app.map.rails[otherIndices[0]][otherIndices[1]]
                    # connect to the other rail if both are multi rails
                    if len(other.directions) > 2:
                        self.connectToRail(other, dif)

    def createAllDirections(self):
        # create all directions
        if len(self.directions) == 2:
            curDirectionList = list(self.directions)
            self.allDirections = [{curDirectionList[0], curDirectionList[1]}]
        else:
            self.allDirections = []
            # hard coded to be sorted...
            if "top" in self.directions and "bottom" in self.directions:
                self.allDirections.append({"top", "bottom"})
            if "left" in self.directions and "right" in self.directions:
                self.allDirections.append({"left", "right"})
            if "top" in self.directions and "left" in self.directions:
                self.allDirections.append({"top", "left"})
            if "top" in self.directions and "right" in self.directions:
                self.allDirections.append({"top", "right"})
            if "bottom" in self.directions and "right" in self.directions:
                self.allDirections.append({"bottom", "right"})
            if "bottom" in self.directions and "left" in self.directions:
                self.allDirections.append({"bottom", "left"})

            # make sure spawnable rails stays spawnable
            if self.spawnCarDirection != None:
                index = len(self.allDirections) - 1
                while index >= 0:
                    curDirection = self.allDirections[index]
                    if self.spawnCarDirection not in curDirection:
                        self.allDirections.remove(curDirection)
                    index -= 1

        # set direction for rail
        self.dirIndex = 0
        self.directions = self.allDirections[self.dirIndex]

    def outOfBoundConnection(self, row, col, spawnableRails):
        if row < 0:
            self.directions.add("top")
            self.spawnCarDirection = "top"
            spawnableRails.append(self)
        elif row >= len(app.map.rails):
            self.directions.add("bottom")
            self.spawnCarDirection = "bottom"
            spawnableRails.append(self)
        if col < 0:
            self.directions.add("left")
            self.spawnCarDirection = "left"
            spawnableRails.append(self)
        elif col >= len(app.map.rails[0]):
            self.directions.add("right")
            self.spawnCarDirection = "right"
            spawnableRails.append(self)

    # endregion

    # region destination generation
    def createDestination(self, map, type, unitSize, app):
        # can't be switchable
        if len(self.allDirections) > 1:
            return False

        # need to be straight
        directionList = list(self.directions)
        if directionList[0] != Rail.directionComplement[directionList[1]]:
            return False

        # not too close with other destinations
        if self.tooClose(map.allDestinations, app):
            return False

        # determine relative positive
        if "top" in self.directions:
            relativePositions = ["left", "right"]
        if "right" in self.directions:
            relativePositions = ["top", "bottom"]

        # random relative position
        random.shuffle(relativePositions)

        # try each relative position
        for relativePos in relativePositions:
            neighborRail = self.neighborRail(map, relativePos)
            if self.checkNeighborForDestination(neighborRail, relativePos):
                newDestination = Destination(
                    (self.indices[0], self.indices[1]), unitSize, type, relativePos
                )
                # add to destination list of both rails
                self.destinationList.append(newDestination)
                neighborRail.destinationList.append(newDestination)
                return True

        # return False if both direction doesn't work
        return False

    def checkNeighborForDestination(self, neighborRail, relativePos):
        # edge rails are not valid
        if neighborRail == None:
            return False

        # can't already have a destination in the same way
        if len(neighborRail.destinationList) == 2:
            return False
        elif len(neighborRail.destinationList) == 1:
            if neighborRail.destinationList[0] == Rail.directionComplement[relativePos]:
                return False

        # can't be switchable
        if len(neighborRail.allDirections) > 1:
            return False

        # need to be straight in the same way
        if self.directions != neighborRail.directions:
            return False

        return True

    def tooClose(self, allDestinations, app):
        # check all destinations
        for destination in allDestinations:
            # check if it is less thatn the minimum difference
            dif = abs(destination.indices[0] - self.indices[0]) + abs(
                destination.indices[1] - self.indices[1]
            )
            if dif < app.minDifBtwDestination:
                return True
        return False

    def neighborRail(self, map, direction):
        dif = Rail.directionToDif[direction]
        newIndices = (self.indices[0] + dif[0], self.indices[1] + dif[1])
        if mapFile.Map.inBound(map, newIndices):
            return map.rails[newIndices[0]][newIndices[1]]

    # endregion
