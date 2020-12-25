import sys, pygame
import math


pygame.init()


# defined constants
dagaSize = 64                                                                   # mobot image size should always be 64x64 px
bgColor = (255, 255, 255)                                                       # purple background
screenSize = (1000, 800)                                                        # fix this to simplify distance scaling and all other calculations
screenCenter = [(0.5*screenSize[0]), (0.5*screenSize[1])]                       # locate center of the screen

gameClock = pygame.time.Clock()

# create screen
screen = pygame.display.set_mode(screenSize)

# title and icon
pygame.display.set_caption('Daga: Remote 2D Space Mapping Project')
icon = pygame.image.load('logo.ico')
pygame.display.set_icon(icon)

# fps display
fpsFont = pygame.font.Font('freesansbold.ttf', 20)
displayFps = True                                                               # set this to True for now
def renderFps(fpsVal):
    fpsText = fpsFont.render("FPS: {}".format(int(fpsVal)), True, (0, 0, 0))
    screen.blit(fpsText, (900, 25))

# bomb count display
bombFont = pygame.font.Font('freesansbold.ttf', 32)
def renderActiveBombs(bombList, bombLimit):
    counter = 0
    for bomb in bombList:
        if bomb.active:
            counter += 1
    bombText = bombFont.render("Bombs Remaining: {}".format(bombLimit - counter), True, (0, 0, 0))
    screen.blit(bombText, (330, 50))

# compass image
compassImg = pygame.image.load('./assets/compass.png').convert_alpha()
compassPos = compassImg.get_rect(center=(64, 64))


# ******************************************************************************
# --- define a mobot object to display mobot location, movement, and oriention
class dagaObject:
    def __init__(self, inputImgPath, inputLoc, inputMoveSpeed, inputRotateSpeed):
        self.imageRef = pygame.image.load(inputImgPath).convert_alpha()
        self.image = self.imageRef.copy()
        self.loc = inputLoc
        self.mSpeed = inputMoveSpeed
        self.rSpeed = inputRotateSpeed
        self.pos = self.image.get_rect(center=(self.loc[0], self.loc[1]))
        self.angle = 0
        self.vDir = None
        self.rDir = None
        self.turnFlag = False
        self.moveFlag = False

    def turn(self):
        if self.rDir == 'ccw':
            self.angle += self.rSpeed
        elif self.rDir == 'cw':
            self.angle -= self.rSpeed
        self.angle = self.angle % 360 
        self.image = pygame.transform.rotate(self.imageRef, self.angle)         # rotate the original image -- to minimize image distortion
        self.pos = self.image.get_rect(center=(self.loc[0], self.loc[1]))       # fix the center location

    def move(self):
        if self.vDir == 'forward':
            angleTemp = self.angle
        elif self.vDir == 'backward':
            if self.angle < 180:
                angleTemp = 180 + self.angle
            else:
                angleTemp = self.angle - 180
        deltaX = self.mSpeed * math.sin(math.radians(angleTemp))                # apparently, the x-axis (0 degress) is vertical here in pygame
        deltaY = self.mSpeed * math.cos(math.radians(angleTemp))                # apparently, the y-axis (90 degress) is horizontal here in pygame
        self.loc[0] = self.loc[0] - deltaX
        self.loc[1] = self.loc[1] - deltaY

        # check if mobot is already at the edge of the screen, keep it inside the screen
        if self.loc[0] <= 0: 
            self.loc[0] = 0
        if self.loc[0] >= screenSize[0]:
            self.loc[0] = screenSize[0]
        if self.loc[1] <= 0: 
            self.loc[1] = 0
        if self.loc[1] >= screenSize[1]:
            self.loc[1] = screenSize[1]
            
        self.pos = self.image.get_rect(center=(self.loc[0], self.loc[1]))
# *** end of dataObject definition

# ******************************************************************************
# --- define a bomb object to define behaviours, timing, and control
class bombObject:
    def __init__(self, _index):
        self.imgDropped = pygame.image.load('./assets/bomb_ready.png').convert_alpha()
        self.imgExplode = pygame.image.load('./assets/bomb_exploded.png').convert_alpha()
        self.pos = None
        self.timer = 3000
        self.timerEvent = pygame.USEREVENT + _index
        pygame.time.set_timer(self.timerEvent , self.timer)
        self.active = False

    def drop(self, _droppedLoc):
        self.pos = self.imgDropped.get_rect(center=(_droppedLoc[0], _droppedLoc[1]))
        screen.blit(self.imgDropped, self.pos)
        self.active = True

    def disappear(self):
        self.active = False
        self.pos = self.pos.move(5000, 5000)
# *** end of bombObject definition


mobot = dagaObject('./assets/dagaPlane.png', screenCenter, 3, 3)
bombIndex = 0
bombDropped = False
bombExpired = False
maxBombs = 5
bombs = []
bombToRemove = None


# ******************************************************************************
# --- GAME LOOP
while True:
    for wEvent in pygame.event.get():
        if wEvent.type == pygame.QUIT:
            sys.exit()
        if wEvent.type == pygame.KEYDOWN:
            if wEvent.key == pygame.K_LEFT:
                mobot.rDir = 'ccw'
                mobot.turnFlag = True
            if wEvent.key == pygame.K_RIGHT:
                mobot.rDir = 'cw'
                mobot.turnFlag = True
            if wEvent.key == pygame.K_UP:
                mobot.vDir = 'forward'
                mobot.moveFlag = True
            if wEvent.key == pygame.K_DOWN:
                mobot.vDir = 'backward'
                mobot.moveFlag = True
        if wEvent.type == pygame.KEYUP:
            if wEvent.key == pygame.K_LEFT or wEvent.key == pygame.K_RIGHT:
                mobot.rDir = None
                mobot.turnFlag = False
            if wEvent.key == pygame.K_UP or wEvent.key == pygame.K_DOWN:
                mobot.vDir = None
                mobot.moveFlag = False
            if wEvent.key == pygame.K_SPACE and not bombDropped:
                bombDropped = True
        for i in range(maxBombs):
            if wEvent.type == pygame.USEREVENT + i:
                bombExpired = True
                bombToRemove = i


    screen.fill(bgColor)                                                        # draw background
    if displayFps:                                                              # display fps
        renderFps(gameClock.get_fps())
    screen.blit(compassImg, compassPos)                                         # draw compass

    if mobot.turnFlag:
        mobot.turn()
    if mobot.moveFlag:
        mobot.move()
    screen.blit(mobot.image, mobot.pos)                                         # draw mobot

    if bombExpired:                                                             # remove any bomb that expired
        bombs[bombToRemove].disappear()
        bombExpired = False
    if bombDropped:                                                             # draw any new bomb that was dropped
        if bombIndex >= maxBombs:
            bombIndex = 0
        if len(bombs) >= maxBombs:
            if bombs[bombIndex].active:
                pass
            else:
                bombs[bombIndex].__init__(bombIndex)
                bombs[bombIndex].drop(mobot.loc)
                bombIndex += 1
        else:
            bombs.append(bombObject(bombIndex))
            bombs[bombIndex].drop(mobot.loc)
            bombIndex += 1
        bombDropped = False
    if bombs:
        for bomb in bombs:
            if bomb.active:
                screen.blit(bomb.imgDropped, bomb.pos)
    
    renderActiveBombs(bombs, maxBombs)

    pygame.display.update()
    gameClock.tick(120)                                                         # limit fps to 120
# *** end of GAME LOOP