""" Air Hockey """

import sys, random
from threading import Thread
import cv2 as cv
import numpy as np 
from cvzone.HandTrackingModule import HandDetector 
import time, serial
from math import sin,cos,tan,atan2,pi,sqrt

if sys.version_info.major > 2:
    import tkinter as tk
else:
    import Tkinter as tk

#### PARAMETER FOR DISPLAY #####
RED, BLACK, WHITE, DARK_RED, BLUE = "red", "black", "white", "dark red", "blue"
ZERO = 2 #for edges.
LOWER, UPPER = "lower", "upper"
HOME, AWAY = "Top", "Bottom"

######## GAME SETTUP - START_SCORE.copy().
START_SCORE = {HOME: 0, AWAY: 0}
MAX_SCORE = 7 # Winning score.
SPEED = 30 # milliseconds between frame update.
FONT = "ms 50"
MAX_PUCK_SPEED= 15 # Speed of puck
PADDLE_SPEED = MAX_PUCK_SPEED*0.8 # Speed of paddle
GOAL_WIDTH_RATIO = 0.1 # Width of goal compare to width of table 

# Table size
SCREEN_X = 1280
SCREEN_Y = 720

# Player paddle setup
X_PADDLE_PLAYER = SCREEN_X - 50
Y_PADDLE_PLAYER = SCREEN_Y/2 
X_PADDLE_PLAYER_PREVIOUS = SCREEN_X - 50
Y_PADDLE_PLAYER_PREVIOUS = SCREEN_Y/2
PADDLE_SIZE = 50
AI_MODE = "attack" # "defend" or "attack"

# Puck setup
X_PUCK = SCREEN_X/2
Y_PUCK = SCREEN_Y/2
PUCK_SIZE = 20

#### CALIBRATION CAM ####
points = [] # select point 
target_points = [(0, 0), (SCREEN_Y, 0), (SCREEN_Y, SCREEN_X/2), (0, SCREEN_X/2)]
HM = None

#### SETUP FOR ARDUINO CONNECTION
port = 'COM11' # Change COM to Bluetooth or Serial
bluetooth = serial.Serial(port, 9600) #Start communications with the bluetooth unit
print("Connected")
bluetooth.flushInput() #This gives the bluetooth a little kick


#### METHODS ####

def str_dict(dic):
    """ Returns a string version of score dictionary - dic """
    return "%s: %d, %s: %d" % (HOME, dic[HOME], AWAY, dic[AWAY])
    
def rand():
    """
    Picks a random tuple to return out of:
    (1, 1), (1, -1), (-1, 1), (-1, -1)
    """
    return random.choice(((1, 1), (1, -1), (-1, 1), (-1, -1))) 

def sign(x):
    return (x > 0) - (x < 0)

 
#### OBJECT DEFINITIONS ####
        
class Equitment(object):
    """
    Parent class of Puck and Paddle.
    canvas: tk.Canvas object.
    width: int, radius of object.
    position: tuple, initial position (x, y).
    color: string, color of object.
    """
    def __init__(self, canvas, width, position, color):
        self.can, self.w = canvas, width
        self.x, self.y = position
        
        self.Object = self.can.create_oval(self.x-self.w, self.y-self.w, 
                                    self.x+self.w, self.y+self.w, fill=color)
    def update(self, position):
        self.x, self.y = position
        self.can.coords(self.Object, self.x-self.w, self.y-self.w,
                                     self.x+self.w, self.y+self.w)
    def __eq__(self, other):
        overlapping = self.can.find_overlapping(self.x-self.w, self.y-self.w,
                                                self.x+self.w, self.y+self.w)
        return other.get_object() in overlapping
        
    def get_width(self):
        return self.w
    def get_position(self):
        return self.x, self.y
    def get_object(self):
        return self.Object
        
class PuckManager(Equitment):
    """
    A black instance of Equitment.
    canvas: tk.Canvas object.
    width: int, radius of puck.
    position: tuple, initial position (x, y).
    """
    def __init__(self, canvas, width, position):
        Equitment.__init__(self, canvas, width, position, BLACK)
        
class Paddle(Equitment):
    """
    A red instance of Equitment with an extra drawing (handle).
    canvas: tk.Canvas object.
    width: int, radius of paddle.
    position: tuple, initial position (x, y).
    """  
    def __init__(self, canvas, width, position, constraint):
        if constraint == UPPER:
            Equitment.__init__(self, canvas, width, position, RED)
            self.handle = self.can.create_oval(self.x-self.w/2, self.y-self.w/2,
                                    self.x+self.w/2, self.y+self.w/2, fill=DARK_RED)
        if constraint == LOWER:
            Equitment.__init__(self, canvas, width, position, WHITE)
            self.handle = self.can.create_oval(self.x-self.w/2, self.y-self.w/2,
                                    self.x+self.w/2, self.y+self.w/2, fill=WHITE)
    def update(self, position):
        Equitment.update(self, position)
        self.can.coords(self.handle, self.x-self.w/2, self.y-self.w/2,
                                   self.x+self.w/2, self.y+self.w/2)
                                   
class Background(object):
    """
    canvas: tk.Canvas object.
    screen: tuple, screen size (w, h).
    goal_w: int, width of the goal.
    """
    def __init__(self, canvas, screen, goal_w):
        self.can, self.goal_w = canvas, goal_w     
        self.w, self.h = screen
        
        self.draw_bg()
    
    def draw_bg(self):
        self.can.config(bg=WHITE, width=self.w, height=self.h)
        ## middle circle
        d = self.goal_w/4
        self.can.create_oval(self.w/2-d, self.h/2-d, self.w/2+d, self.h/2+d, 
                                                     fill=WHITE, outline=BLUE)
        ## Boundary lines
        self.can.create_line(self.w/2, ZERO, self.w/2, self.h, fill=BLUE) #middle
        self.can.create_line(ZERO, ZERO, self.w, ZERO, fill=BLUE) # top
        self.can.create_line(ZERO, self.h, self.w, self.h, fill=BLUE) # bottom
        
        self.can.create_line(ZERO, ZERO, ZERO,self.h/2-self.goal_w/2, fill=BLUE)  
        self.can.create_line(ZERO, self.h/2 + self.goal_w/2, ZERO, self.h, fill=BLUE)

        self.can.create_line(self.w, ZERO, self.w, self.h/2-self.goal_w/2, fill=BLUE)  
        self.can.create_line(self.w, self.h/2 + self.goal_w/2, self.w, self.h, fill=BLUE)       
                                                                     
    def is_position_valid(self, position, width, constraint=None):
        x, y = position
        #if puck is in goal, let it keep going in.
        if constraint == None and self.is_in_goal(position, width):
            return True
        elif (x - width < ZERO or x + width > self.w or 
            y - width < ZERO or y + width > self.h):
            return False
        elif constraint == LOWER:
            return x - width > self.w/2
        elif constraint == UPPER:
            return x + width < self.w/2
        else:
            return True    

    def is_in_goal(self, position, width):
        x, y = position
        if (x - width <= ZERO and y - width > self.h/2 - self.goal_w/2 and 
                                    y + width < self.h/2 + self.goal_w/2):
            return HOME
        elif (x + width >= self.w and y - width > self.h/2 - self.goal_w/2 and 
                                        y + width < self.h/2 + self.goal_w/2):
            return AWAY
        else:
            return False
            
    def get_screen(self):
        return self.w, self.h   
    def get_goal_w(self):
        return self.goal_w
        
class Puck(object):
    """
    canvas: tk.Canvas object.
    background: Background object.
    """
    def __init__(self, canvas, background):
        self.background = background
        self.screen = self.background.get_screen()
        self.x, self.y = X_PUCK, Y_PUCK
        # self.can, self.w = canvas, self.background.get_goal_w()/12
        self.can, self.w = canvas, PUCK_SIZE
        c, d = rand() #generate psuedorandom directions.
        velocity = MAX_PUCK_SPEED
        self.vx, self.vy = velocity*c, velocity*d
        self.angle = atan2(self.vy, self.vx)
        self.a = 1.0 #friction
        self.cushion = self.w*0.25
        
        self.puck = PuckManager(canvas, self.w, (self.y, self.x))
        
    def update(self):
        #air hockey table - puck never completely stops.
        # if self.vx > 0.25: self.vx *= self.a
        # if self.vy > 0.25: self.vy *= self.a

        x, y = self.x + self.vx, self.y + self.vy #predict
        if not self.background.is_position_valid((x, y), self.w):
            if self.x - self.w < ZERO or self.x + self.w > self.screen[0]:
                # self.vx *= -1
                self.angle = pi - self.angle
            if self.y - self.w < ZERO or self.y + self.w > self.screen[1]:
                # self.vy *= -1
                self.angle = - self.angle
                
            # x, y = self.x+self.vx, self.y+self.vy
        
        # Update velocity
        self.vx = MAX_PUCK_SPEED*cos(self.angle)
        self.vy = MAX_PUCK_SPEED*sin(self.angle)   
        if abs(self.vx) == 0: self.vx += random.uniform(0, 1)
        if abs(self.vy) == 0: self.vy += random.uniform(0, 1)
        # Update position
        x, y = self.x + self.vx, self.y + self.vy 
        self.x, self.y = x, y
        self.puck.update((self.x, self.y))

    def get_position(self):
        return (self.x, self.y)

    def hit(self, paddle, moving = False):
        # Update velocity of ball
        x_paddle, y_paddle = paddle.get_position()
        delta_x = self.x - x_paddle
        delta_y = self.y - y_paddle
        self.angle = atan2(delta_y,delta_x)

        # Publish a vibration signal 
        # bluetooth.write(str.encode(str(1)))
    
    def __eq__(self, other):
        return other == self.puck
    def in_goal(self):
        return self.background.is_in_goal((self.x, self.y), self.w)

class Player(object):
    """
    master: tk.Tk object.
    canvas: tk.Canvas object.
    background: Background object.
    puck: Puck object.
    constraint: UPPER or LOWER (can be None).
    """
    def __init__(self, master, canvas, background, puck, constraint):
        self.puck, self.background = puck, background
        self.constraint, self.v = constraint, PADDLE_SPEED
        self.ai_mode = AI_MODE
        screen = self.background.get_screen()
        self.y = Y_PADDLE_PLAYER
        self.x = 100 if self.constraint == UPPER else X_PADDLE_PLAYER

        self.paddle = Paddle(canvas, PADDLE_SIZE, (self.x, self.y),constraint)
        self.up, self.down, self.left, self.right = False, False, False, False
        
        if self.constraint == LOWER:
            master.bind('<Up>', self.MoveUp)
            master.bind('<Down>', self.MoveDown)
            master.bind('<KeyRelease-Up>', self.UpRelease)
            master.bind('<KeyRelease-Down>', self.DownRelease)
            master.bind('<Right>', self.MoveRight)
            master.bind('<Left>', self.MoveLeft)
            master.bind('<KeyRelease-Right>', self.RightRelease)
            master.bind('<KeyRelease-Left>', self.LeftRelease)
        else:
            master.bind('<w>', self.MoveUp)
            master.bind('<s>', self.MoveDown)
            master.bind('<KeyRelease-w>', self.UpRelease)
            master.bind('<KeyRelease-s>', self.DownRelease)
            master.bind('<d>', self.MoveRight)
            master.bind('<a>', self.MoveLeft)
            master.bind('<KeyRelease-d>', self.RightRelease)
            master.bind('<KeyRelease-a>', self.LeftRelease)
        
    def update(self):
        x, y = self.x, self.y # paddle
        x_puck, y_puck = self.puck.get_position() # puck 
        vel_x_puck = self.puck.vx

        ## AI PLAYER        
        if self.constraint == UPPER:
            if self.ai_mode == "defend":
                if (x_puck < SCREEN_X/2 + 30 )and x_puck > x and vel_x_puck < 0:
                    if abs(y_puck-y) - (PUCK_SIZE+PADDLE_SIZE) > 5:
                        y = self.y + sign((y_puck-y) - (PUCK_SIZE+PADDLE_SIZE))*self.v
                    # if y_puck-y > (PUCK_SIZE+PADDLE_SIZE): y = self.y + self.v
                    # elif y_puck-y < -(PUCK_SIZE+PADDLE_SIZE): y = self.y - self.v
                else: 
                    if abs(SCREEN_Y/2 - y) > 5: 
                        y = self.y + sign(SCREEN_Y/2 - y)*self.v
            
            elif self.ai_mode == "attack":
                if (x_puck < SCREEN_X/2 + 30 ) and x_puck > 100:
                    if abs(y_puck-y) - (PUCK_SIZE+PADDLE_SIZE) > 2:
                        y = self.y + sign((y_puck-y) - (PUCK_SIZE+PADDLE_SIZE))*self.v
                    if (x_puck < SCREEN_X/2 - 50) and abs(x_puck - x) - (PUCK_SIZE+PADDLE_SIZE) > 2: 
                        x = self.x + sign((x_puck-x) - (PUCK_SIZE+PADDLE_SIZE))*self.v
                
                else:
                    if abs(SCREEN_Y/2 - y) > 5:
                        y = self.y + sign(SCREEN_Y/2 - y)*self.v
                    if abs(100 - x) > 5: 
                        x = self.x + sign(100 - x)*self.v
        
        ## HUMAN PLAYER
        if self.constraint == LOWER:
            x = X_PADDLE_PLAYER
            y = Y_PADDLE_PLAYER
        
        ## Check the position of paddle
        if self.background.is_position_valid((x, y), self.paddle.get_width(), self.constraint):
            self.x, self.y = x, y
            self.paddle.update((self.x, self.y))
        
        ## Check the collision 
        if sqrt((self.x-x_puck)**2 + (self.y-y_puck)**2) <= (PUCK_SIZE + PADDLE_SIZE + 1):
            self.puck.hit(self.paddle)
        
        ## Check 

    def MoveUp(self, callback=False):
        self.up = True
    def MoveDown(self, callback=False):
        self.down = True
    def MoveLeft(self, callback=False):
        self.left = True
    def MoveRight(self, callback=False):
        self.right = True
    def UpRelease(self, callback=False):
        self.up = False
    def DownRelease(self, callback=False):
        self.down = False
    def LeftRelease(self, callback=False):
        self.left = False
    def RightRelease(self, callback=False):
        self.right = False
        
class Home(object):
    """
    Game Manager.
    master: tk.Tk object.
    screen: tuple, screen size (w, h).
    score: dict.
    """
    def __init__(self, master, screen, score=START_SCORE.copy()):
        self.frame = tk.Frame(master)
        self.frame.pack()
        self.can = tk.Canvas(self.frame)
        self.can.pack()
        #goal width = 1/3 of screen width
        background = Background(self.can, screen, screen[1]*GOAL_WIDTH_RATIO)
        self.puck = Puck(self.can, background)
        self.p1 = Player(master, self.can, background, self.puck, UPPER)
        self.p2 = Player(master, self.can, background, self.puck, LOWER)
        
        master.bind("<Return>", self.reset)
        master.bind("<r>", self.reset)
        
        master.title(str_dict(score))
        
        self.master, self.screen, self.score = master, screen, score
        
        self.update()
        
    def reset(self, callback=False):
        """ <Return> or <r> key. """
        if callback.keycode == 82: #r key resets score.
            self.score = START_SCORE.copy()
        self.frame.destroy()
        self.__init__(self.master, self.screen, self.score)
        
    def update(self):
        self.puck.update()
        self.p1.update()
        self.p2.update()
        if not self.puck.in_goal():
            self.frame.after(SPEED, self.update) 
        else:
            winner = HOME if self.puck.in_goal() == AWAY else AWAY
            self.update_score(winner)
            
    def update_score(self, winner):
        self.score[winner] += 1
        self.master.title(str_dict(self.score))
        if self.score[winner] == MAX_SCORE:
            self.frame.bell()
            self.can.create_text(self.screen[0]/2, self.screen[1]/2, font=FONT,
                                                     text="%s wins!" % winner, angle=90)
            self.score = START_SCORE.copy()
        else:
            self.can.create_text(self.screen[0]/2, self.screen[1]/2, font=FONT,
                                                 text="Point for %s" % winner, angle=90)
                                                 
def play():
    """ screen: tuple, screen size (w, h). """
    root = tk.Tk()
    screen = SCREEN_X,SCREEN_Y
    Home(root, screen)
    time.sleep(1)
    root.mainloop()

'''
CAMERA
'''
## Detect Hand 
hand_detector = HandDetector(maxHands=1, detectionCon=0.8) 
def hand_detect(img):
    hands, img = hand_detector.findHands(img, draw=True)      
    x_center = None; y_center= None
    if hands:
        hand = hands[0]
        center = hand['center']
        x_center = center[0]; y_center = center[1]
        img = cv.circle(img, center, 3, (0,255,0), 2)
    return img, x_center, y_center

## Function to handle mouse clicks
def mouse_callback(event, x, y, flags, param):
    global points
    if event == cv.EVENT_LBUTTONDOWN:
        points.append([x, y])

## Calibrate Camera 
def calibrate():
    global HM, points, target_points, SCREEN_Y, SCREEN_X
    cap = cv.VideoCapture(1, cv.CAP_DSHOW)
    while (cap.isOpened() and len(points) < 4):
        _, frame = cap.read()

        cv.imshow("Image",frame)  
        cv.setMouseCallback("Image", mouse_callback)
        for point in points:
            cv.circle(frame, (point[0], point[1]), 5, (0,255,0), -1)
            cv.imshow("Image", frame)

        if cv.waitKey(10) == 27:
            break 

        # else:
        #     src_points = np.array(points, dtype=np.float32)
        #     dst_points = np.array(target_points, dtype=np.float32)
        #     HM = cv.getPerspectiveTransform(src_points, dst_points)
        #     warped = cv.warpPerspective(frame, HM, (int(SCREEN_Y), int(SCREEN_X/2)))
        #     cv.imshow("Image", warped)

    cv.destroyAllWindows()
    # Find HM 
    src_points = np.array(points, dtype=np.float32)
    dst_points = np.array(target_points, dtype=np.float32)
    HM = cv.getPerspectiveTransform(src_points, dst_points)

def camera():
    global X_PADDLE_PLAYER, X_PADDLE_PLAYER_PREVIOUS
    global Y_PADDLE_PLAYER, Y_PADDLE_PLAYER_PREVIOUS
    global SCREEN_X
    global SCREEN_Y

    cap = cv.VideoCapture(1, cv.CAP_DSHOW)
    while (cap.isOpened()):
        
        # Capture frame 
        _, frame = cap.read()
        # frame = cv.flip(frame, 1) # flip frame

        # Warp Resize
        frame = cv.warpPerspective(frame, HM, (int(SCREEN_Y), int(SCREEN_X/2)))
        
        # # detection 
        frame_new, x_center, y_center = hand_detect(frame)
        if (x_center is not None) and (y_center is not None): 
            Y_PADDLE_PLAYER = x_center
            X_PADDLE_PLAYER = y_center + SCREEN_X/2     
            
        # check
        if abs(X_PADDLE_PLAYER-X_PADDLE_PLAYER_PREVIOUS) < 2:
            X_PADDLE_PLAYER = X_PADDLE_PLAYER_PREVIOUS
        if abs(Y_PADDLE_PLAYER-Y_PADDLE_PLAYER_PREVIOUS) < 2:
            Y_PADDLE_PLAYER = Y_PADDLE_PLAYER_PREVIOUS

        # update previous
        X_PADDLE_PLAYER_PREVIOUS = X_PADDLE_PLAYER 
        Y_PADDLE_PLAYER_PREVIOUS = Y_PADDLE_PLAYER
        # Show 
        cv.imshow("video", frame_new)
        # 
        key = cv.waitKey(30)
        if key == 27:
            break 

    cap.release()
    cv.destroyAllWindows()

            
if __name__ == "__main__":
    """ Choose screen size """  
    calibrate()
    show_thread = Thread(target=camera)
    show_thread.start()
    show_thread = Thread(target=play)
    show_thread.start()