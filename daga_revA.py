import sys, pygame
import math

pygame.init()


# defined constants
dagaSize = 64                                                                   # mobot image size should always be 64x64 px
bgColor = (255, 255, 255)                                                       # purple background
screenSize = (1000, 800)                                                        # fix this to simplify distance scaling and all other calculations
screenCenter = [(0.5*screenSize[0]), (0.5*screenSize[1])]                       # locate center of the screen


# game globals
gameClock = pygame.time.Clock()
gameIsOnStart = False                                                           # set this to false for now
gameIsActive = True                                                             # set this to True for now
gameIsOver = False                                                              # set this to False for now
score = 0
hiScore = 0
maxBombs = 5
bombs = []
bombIndex = 0
bombDropped = False
bombExploded = False
bombExpired = False
bombToRemove = None
bombToExplode = None


# create screen
screen = pygame.display.set_mode(screenSize)


# title and icon
pygame.display.set_caption('Daga: Remote 2D Space Mapping Project')
icon = pygame.image.load('logo.ico')
pygame.display.set_icon(icon)


# top UI
fpsFont = pygame.font.Font('freesansbold.ttf', 16)
bombFont = pygame.font.Font('freesansbold.ttf', 24)
scoreFont = pygame.font.Font('freesansbold.ttf', 36)
hiScoreFont = pygame.font.Font('freesansbold.ttf', 24)
compassImg = pygame.image.load('./assets/compass.png').convert_alpha()
compassPos = compassImg.get_rect(center=(75, 75))
uiMargin = [(5,5), (5,145), (995, 145), (995, 5)]

def renderTopUI(fpsVal, bombList, bombLimit):
    # render margin
    pygame.draw.polygon(screen, (0,0,0), uiMargin, width=3)

    # render compass
    screen.blit(compassImg, compassPos)                                         # draw compass

    # render fps
    fpsText = fpsFont.render("FPS: {}".format(int(fpsVal)), True, (0, 0, 0))
    screen.blit(fpsText, (900, 25))

    # render remaining bombs
    if gameIsActive:
        counter = 0
        for bomb in bombList:
            if bomb.active:
                counter += 1
        if counter < bombLimit:
            bombText = bombFont.render("Bombs Remaining: {}".format(bombLimit - counter), True, (0, 0, 0))
        else:
            bombText = bombFont.render("Bombs Remaining: {}".format(bombLimit - counter), True, (255, 0, 0))
        screen.blit(bombText, (375, 100))

    # render Score
    scoreText = scoreFont.render("SCORE: {}".format(score), True, (0, 0, 0))
    screen.blit(scoreText, (410, 50))

    # render High Score
    hiScoreText = hiScoreFont.render("HIGH SCORE: {}".format(hiScore), True, (0, 0, 0))
    screen.blit(hiScoreText, (750, 100))


# ******************************************************************************
# --- define a mobot object to display mobot location, movement, and oriention
class dagaObject:
    def __init__(self, _loc, _mSpeed, _rSpeed):
        self.imageRef = pygame.image.load('./assets/dagaPlane.png').convert_alpha()
        self.image = self.imageRef.copy()
        self.loc = _loc
        self.mSpeed = _mSpeed
        self.rSpeed = _rSpeed
        self.pos = self.image.get_rect(center=(self.loc[0], self.loc[1]))
        self.angle = 0
        self.hDir = None                                                        # True if FORWARD, False if BACKWARD
        self.rDir = None                                                        # True if CCW, False if CW
        self.turnFlag = False
        self.moveFlag = False

    def turn(self):
        if self.rDir == True:
            self.angle += self.rSpeed
        elif self.rDir == False:
            self.angle -= self.rSpeed
        self.angle = self.angle % 360 
        self.image = pygame.transform.rotate(self.imageRef, self.angle)         # rotate the original image -- to minimize image distortion
        self.pos = self.image.get_rect(center=(self.loc[0], self.loc[1]))       # fix the center location

    def move(self):
        if self.hDir == True:
            angleTemp = self.angle
        elif self.hDir == False:
            if self.angle < 180:
                angleTemp = 180 + self.angle
            else:
                angleTemp = self.angle - 180
        deltaX = self.mSpeed * math.sin(math.radians(angleTemp))                # apparently, the x-axis (0 degress) is vertical here in pygame
        deltaY = self.mSpeed * math.cos(math.radians(angleTemp))                # apparently, the y-axis (90 degress) is horizontal here in pygame
        self.loc[0] = self.loc[0] - deltaX
        self.loc[1] = self.loc[1] - deltaY

        # check if mobot is already at the edge of the screen, keep it inside the screen
        if self.loc[0] <= dagaSize*0.5: 
            self.loc[0] = dagaSize*0.5
        if self.loc[0] >= screenSize[0] - (dagaSize*0.5):
            self.loc[0] = screenSize[0] - (dagaSize*0.5)
        if self.loc[1] <= 150 + dagaSize*0.5: 
            self.loc[1] = 150 + dagaSize*0.5
        if self.loc[1] >= screenSize[1] - (dagaSize*0.5):
            self.loc[1] = screenSize[1] - (dagaSize*0.5)
            
        self.pos = self.image.get_rect(center=(self.loc[0], self.loc[1]))
# *** end of dataObject definition

# ******************************************************************************
# --- define a bomb object to define behaviours, timing, and control
class bombObject:
    def __init__(self, _index):
        self.imgDropped = pygame.image.load('./assets/bomb_ready.png').convert_alpha()
        self.imgExplode = pygame.image.load('./assets/bomb_exploded.png').convert_alpha()
        self.imgage = None
        self.pos = None
        self.timerDrop = 3000
        self.timerDropEvent = pygame.USEREVENT + _index
        self.timerFire = 1000
        self.timerFireEvent = pygame.USEREVENT + 10 + _index                    # put a +10 offset so USEREVENTs are unique
        self.active = False

    def drop(self, _droppedLoc):
        self.active = True
        self.fire = False
        self.image = self.imgDropped.copy()                                     # use dropped version of the bomb
        pygame.time.set_timer(self.timerDropEvent , self.timerDrop)             # start the dropped timer here
        self.pos = self.imgDropped.get_rect(center=(_droppedLoc[0], _droppedLoc[1]))

    def explode(self):
        if self.active:
            self.active = True
            self.image = self.imgExplode.copy()                                 # use explode version of the bomb
            pygame.time.set_timer(self.timerFireEvent , self.timerFire)         # start the explode timer here
        else:
            pass

    def disappear(self):
        self.active = False
        pygame.time.set_timer(self.timerFireEvent , 0)                          # disable drop event timer
        pygame.time.set_timer(self.timerFireEvent , 0)                          # disable explode event timer
        #self.pos = self.pos.move(5000, 5000)
# *** end of bombObject definition


# create player object
mobot = dagaObject(screenCenter, 3, 3)


# ******************************************************************************
# --- GAME LOOP
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                mobot.rDir = True
                mobot.turnFlag = True
            if event.key == pygame.K_RIGHT:
                mobot.rDir = False
                mobot.turnFlag = True
            if event.key == pygame.K_UP:
                mobot.hDir = True
                mobot.moveFlag = True
            if event.key == pygame.K_DOWN:
                mobot.hDir = False
                mobot.moveFlag = True
            if event.key == pygame.K_SPACE and not bombDropped:
                bombDropped = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                mobot.rDir = None
                mobot.turnFlag = False
            if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                mobot.hDir = None
                mobot.moveFlag = False
            if event.key == pygame.K_SPACE:
                bombDropped = False
        for i in range(maxBombs):
            if event.type == pygame.USEREVENT + i:
                bombExploded = True
                bombToExplode = i
        for i in range(maxBombs):
            if event.type == pygame.USEREVENT + 10 + i:
                bombExpired = True
                bombToRemove = i

    screen.fill(bgColor)                                                        # draw background    

    if gameIsActive:
        if mobot.turnFlag:
            mobot.turn()
        if mobot.moveFlag:
            mobot.move()
        screen.blit(mobot.image, mobot.pos)                                     # draw mobot

        if bombExploded:                                                        # changed bomb image to exploded version, start explode timer
            bombs[bombToExplode].explode()
            bombExploded = False
        if bombExpired:                                                         # remove any bomb that expired
            bombs[bombToRemove].disappear()
            bombExpired = False
        if bombDropped:                                                         # draw any new bomb that was dropped
            if bombIndex >= maxBombs:
                bombIndex = 0
            if len(bombs) >= maxBombs:
                if bombs[bombIndex].active:                                     # do not draw bomb if current bomb index is still active
                    pass
                else:
                    bombs[bombIndex].__init__(bombIndex)                        # reinitialize bomb
                    bombs[bombIndex].drop(mobot.loc)                            # reactivate bomb status, start drop timer, update location
                    bombIndex += 1                                              
            else:
                bombs.append(bombObject(bombIndex))                             # if bomb list is not full
                bombs[bombIndex].drop(mobot.loc)                                # activate the bomb, start timer, define location
                bombIndex += 1
            bombDropped = False
        for bomb in bombs:                                                      # draw only active bombs
            if bomb.active:
                screen.blit(bomb.image, bomb.pos)

    renderTopUI(gameClock.get_fps(), bombs, maxBombs)                           # draw all elements of the top UI
    pygame.display.update()
    gameClock.tick(120)                                                         # limit fps to 120
# *** end of GAME LOOP