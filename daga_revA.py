import sys, pygame
import math
import random

pygame.init()

# defined constants
fps = 60
dagaSize = 64                                                                   # mobot image size should always be 64x64 px
backgroundColor = (255, 255, 255)                                               # white background
screenSize = (1000, 800)                                                        # fix this to simplify distance scaling and all other calculations
screenCenter = [(0.5*screenSize[0]), (0.5*screenSize[1])]                       # locate center of the screen


# game globals
timerSeconds = 300
gameIsOnStart = False                                                           # set this to false for now
gameIsActive = True                                                             # set this to True for now
gameIsOver = False                                                              # set this to False for now
score = 0
hiScore = 0
maxBombs = 5
bombs = []
bombIndex = 0
maxMonsters = 5
monsters = []
monsterIndex = 0
bombDropped = False
bombExploded = False
bombExpired = False
bombToRemove = None
bombToExplode = None
spawnMonster = False


# create screen
screen = pygame.display.set_mode(screenSize) 


# title and icon
pygame.display.set_caption('Daga: Remote 2D Space Mapping Project')
icon = pygame.image.load('logo.ico')
pygame.display.set_icon(icon)


# top UI
fpsFont = pygame.font.Font('./fonts/zorque.ttf', 16)
timerFont = pygame.font.Font('./fonts/zorque.ttf', 24)
hpFont = pygame.font.Font('./fonts/zorque.ttf', 32)
bombFont = pygame.font.Font('./fonts/zorque.ttf', 32)
scoreFont = pygame.font.Font('./fonts/zorque.ttf', 40)
hiScoreFont = pygame.font.Font('./fonts/zorque.ttf', 24)
compassImg = pygame.image.load('./images/compass.png').convert_alpha()
compassPos = compassImg.get_rect(center=(75, 75))
heartImg = pygame.image.load('./images/heart.png').convert_alpha()
heartPos = heartImg.get_rect(center=(230, 100))
uiMargin = [(5,5), (5,145), (995, 145), (995, 5)]

def renderTopUI(fpsVal, bombList, bombLimit, hpLeft, timeLeft):
    pygame.draw.polygon(screen, (0,0,0), uiMargin, width=3)
    screen.blit(compassImg, compassPos)

    hpText = hpFont.render('{}'.format(hpLeft), True, (0, 100, 0))
    screen.blit(hpText, (200, 30))
    screen.blit(heartImg, heartPos)

    timerText = timerFont.render('Time Left: {} s'.format(timeLeft), True, (0, 0, 255))
    screen.blit(timerText, (400, 110))

    fpsText = fpsFont.render('FPS: {}'.format(int(fpsVal)), True, (0, 0, 0))
    screen.blit(fpsText, (925, 10))

    counter = 0
    for bomb in bombList:
        if bomb.active:
            counter += 1
    if counter < bombLimit:
        bombText = bombFont.render('Bombs Remaining: {}'.format(bombLimit - counter), True, (0, 0, 0))
    else:
        bombText = bombFont.render('Bombs Remaining: {}'.format(bombLimit - counter), True, (255, 0, 0))
    screen.blit(bombText, (330, 70))

    scoreText = scoreFont.render('SCORE: {}'.format(score), True, (0, 0, 0))
    screen.blit(scoreText, (400, 15))

    hiScoreText = hiScoreFont.render('HIGH SCORE: {}'.format(hiScore), True, (0, 0, 0))
    screen.blit(hiScoreText, (775, 110))


class playerObject:
    def __init__(self):
        self.imageRef = pygame.image.load('./images/dagaPlane.png').convert_alpha()
        self.image = self.imageRef.copy()
        self.loc = screenCenter
        self.mSpeed = 4
        self.rSpeed = 4
        self.pos = self.image.get_rect(center=(self.loc[0], self.loc[1]))
        self.angle = 0
        self.hDir = None                                                        # True if FORWARD, False if BACKWARD
        self.rDir = None                                                        # True if CCW, False if CW
        self.turnFlag = False
        self.moveFlag = False
        self.lifePoints = 1000
        self.crashed = False
        self.burned = False

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


class bombObject:
    def __init__(self, _index):
        self.imgDropped = pygame.image.load('./images/bomb_ready.png').convert_alpha()
        self.imgExplode = pygame.image.load('./images/bomb_exploded.png').convert_alpha()
        self.image = None
        self.pos = None
        self.timerDrop = 2000
        self.timerDropEvent = pygame.USEREVENT + _index
        self.timerFire = 500
        self.timerFireEvent = pygame.USEREVENT + 10 + _index                    # put a +10 offset so USEREVENTs are unique
        self.active = False
        self.onFire = False

    def drop(self, _droppedLoc):
        self.active = True
        self.onFire = False
        self.image = self.imgDropped.copy()                                     # use dropped version of the bomb
        pygame.time.set_timer(self.timerDropEvent , self.timerDrop)             # start the dropped timer here
        self.pos = self.imgDropped.get_rect(center=(_droppedLoc[0], _droppedLoc[1]))

    def explode(self):
        if self.active:
            self.onFire = True
            self.image = self.imgExplode.copy()                                 # use explode version of the bomb
            pygame.time.set_timer(self.timerFireEvent , self.timerFire)         # start the explode timer here

    def disappear(self):
        self.active = False
        self.onFire = False
        pygame.time.set_timer(self.timerDropEvent , 0)                          # disable drop event timer
        pygame.time.set_timer(self.timerFireEvent , 0)                          # disable explode event timer
        #self.pos = self.pos.move(5000, 5000)


class monsterObject:
    def __init__(self):
        self.imgMonsterA = pygame.image.load('./images/monster.png').convert_alpha()
        self.image = self.imgMonsterA.copy()
        self.pos = None
        self.loc = [random.randint(100,900), random.randint(250,700)]
        self.mSpeed = random.randint(1,3) 
        self.path = random.choice([True, False])                                # True if vertical, False if horizontal
        self.dir = random.choice([True, False])                                 # True if upw/right, False if down/left
        self.alive = True
        self.move()

    def move(self):
        if self.alive:
            if self.path == True:                                               # vertical motion
                if self.dir == True:                                            # upward
                    self.loc[1] -= self.mSpeed
                else:                                                           # downward
                    self.loc[1] += self.mSpeed
            else:                                                               # horizontal motion
                if self.dir == True:                                            # right
                    self.loc[0] += self.mSpeed
                else:                                                           # left
                    self.loc[0] -= self.mSpeed
            if self.loc[0] < 50 or self.loc[0] > 950 or self.loc[1] < 200 or self.loc[1] > 750:
                self.dir = not self.dir
            self.pos = self.image.get_rect(center=(self.loc[0], self.loc[1]))

    def kill(self):
        self.alive = False


mobot = playerObject()

gameClock = pygame.time.Clock()
timerEvent = pygame.USEREVENT + 20
pygame.time.set_timer(timerEvent, 1000)

monsterSpawnTimer = 2000
monsterSpawnEvent = pygame.USEREVENT + 21
pygame.time.set_timer(monsterSpawnEvent , monsterSpawnTimer)


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
        if event.type == pygame.USEREVENT + 20:
            timerSeconds -= 1 
        if event.type == pygame.USEREVENT + 21:
            spawnMonster = True

    screen.fill(backgroundColor)

    if gameIsActive:
        # --- move mobot
        if mobot.turnFlag:
            mobot.turn()
        if mobot.moveFlag:
            mobot.move()
        screen.blit(mobot.image, mobot.pos)
        
        # --- move/spawn enemies
        if spawnMonster:
            if monsterIndex >= maxMonsters:
                monsterIndex = 0
            if len(monsters) >= maxMonsters:
                for monster in monsters:
                    if not monster.alive:
                        monster.__init__()
                        break
            else:
                monsters.append(monsterObject())
            spawnMonster = False
        for monster in monsters:
            monster.move()

        # --- drop/update bombs
        if bombExploded:
            bombs[bombToExplode].explode()                                      # changed bomb image to exploded version, start explode timer
            bombExploded = False
        if bombExpired:                                                         # remove any bomb that expired
            bombs[bombToRemove].disappear()
            bombExpired = False
        if bombDropped:                                                         # draw any new bomb that was dropped
            if bombIndex >= maxBombs:
                bombIndex = 0
            if len(bombs) >= maxBombs:
                if bombs[bombIndex].active:                                     # do not draw bomb if bomb in current index is still active
                    pass
                else:
                    bombs[bombIndex] = bombObject(bombIndex)                    # reinitialize bomb
                    bombs[bombIndex].drop(mobot.loc)                            # reactivate bomb status, start drop timer, update location
                    bombIndex += 1                                              
            else:
                bombs.append(bombObject(bombIndex))                             # if bomb list is not full, append new bomb object
                bombs[bombIndex].drop(mobot.loc)                                # activate the bomb, start timer, define location
                bombIndex += 1
            bombDropped = False
        for bomb in bombs:                                                      # draw all active bombs
            if bomb.active:
                if bomb.onFire:
                    if bomb.pos.colliderect(mobot.pos):
                        mobot.burned = True
                        mobot.lifePoints -= 1
                    else:
                        mobot.burned = False
                    for monster in monsters:
                        if bomb.pos.colliderect(monster.pos):                   # check bomb and monster collision
                            monster.kill()
                            bomb.disappear()
                            score += 1
                screen.blit(bomb.image, bomb.pos)                
        for monster in monsters:                                                # draw all enemies that are alive
            if monster.alive:
                if monster.pos.colliderect(mobot.pos):
                    mobot.crashed = True
                    mobot.lifePoints -= 2
                else:
                    mobot.crashed = False
                screen.blit(monster.image, monster.pos)
    
    # draw all elements of the top UI
    renderTopUI(gameClock.get_fps(), bombs, maxBombs, mobot.lifePoints, timerSeconds)
    
    pygame.display.update()
    gameClock.tick(fps)