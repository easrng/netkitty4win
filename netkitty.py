from sys import platform
import tkinter as tk
import math, time, random, json, threading
import urllib.request
root = tk.Tk()
from html.parser import HTMLParser
from tkinter import messagebox
from ctypes import windll
windll.shcore.SetProcessDpiAwareness(2)
class HTMLFilter(HTMLParser):
    text = ''
    def handle_data(self, data):
        self.text += f'{data}\n'

def html2text(html):
    filter = HTMLFilter()
    filter.feed(html)

    return filter.text

last_post_id=None
messagelock = threading.Lock()
message = None
def check_netkitty_post():
    global last_post_id, message
    try:
        request_url = urllib.request.urlopen('https://cybre.space/api/v1/accounts/64542/statuses?limit=1&exclude_replies=true')
        post=json.loads(request_url.read())[0]
        if(post['id'] != last_post_id):
            messagelock.acquire()
            message=html2text(post['content']);
            last_post_id=post['id']
            messagelock.release()
    except:
        pass

def poll_netkitty_post():
    while True:
        check_netkitty_post()
        time.sleep(120)

pollthread = threading.Thread(target=poll_netkitty_post)
pollthread.start() 

sprite = tk.PhotoImage(file='netkitty.gif')
def subimage(l, t, r, b):
    dst = tk.PhotoImage()
    dst.tk.call(dst, 'copy', sprite, '-from', l, t, r, b, '-to', 0, 0)
    return dst

images=[[subimage(32*i, 32*j, 32*(i+1), 32*(j+1)) for i in range(8)] for j in range(4)]
spriteSets={"idle":[[3,3]],"alert":[[7,3]],"scratch":[[5,0],[6,0],[7,0]],"tired":[[3,2]],"sleeping":[[2,0],[2,1]],"N":[[1,2],[1,3]],"NE":[[0,2],[0,3]],"E":[[3,0],[3,1]],"SE":[[5,1],[5,2]],"S":[[6,3],[7,2]],"SW":[[5,3],[6,1]],"W":[[4,2],[4,3]],"NW":[[1,0],[1,1]]}
root.image=images[3][3]
frameCount =0
idleTime =0
nekoPosX=32
nekoPosY=32
idleAnimation =None
idleAnimationFrame =0
nekoSpeed = 10
display = tk.Canvas(root, bd=0, highlightthickness=0, bg='#ff0')
display.create_image(0, 0, image=root.image, anchor=tk.NW, tags="IMG")
root.overrideredirect(True)
root.geometry('32x32')
root.lift()
root.wm_attributes("-topmost", True)
root.wm_attributes("-disabled", True)
root.wm_attributes("-transparentcolor", "#ff0")
root.normalicon=subimage(256, 0, 384, 128)
root.alerticon=subimage(384, 0, 512, 128)
root.iconphoto(True, root.normalicon)
root.title("netkitty")
display.grid()

direction = ""

zoomcache={}
zoomcachelevel=None
def setSprite(name, frame, scale):
    global zoomcache, zoomcachelevel
    (x, y) = spriteSets[name][frame % len(spriteSets[name])]
    if zoomcachelevel != scale:
        print("dpi change, resizing sprites")
        zoomcache={}
        zoomcachelevel=scale
        i=0
        for x in range(8):
            for y in range(4):
                ck='{x}x{y}'.format(x=x,y=y)
                zoomcache[ck]=images[y][x].zoom(scale,scale)
                i+=1
                print(i, "of", 4*8)
        print("done")
    nekoSize=math.floor(scale*32)
    ck='{x}x{y}'.format(x=x,y=y)
    root.image=zoomcache[ck]
    if name == "alert":
        root.iconphoto(True, root.alerticon)
    else:
        root.iconphoto(True, root.normalicon)
    display.delete("IMG")
    root.geometry('{s}x{s}'.format(s=nekoSize))
    display.create_image(0, 0, image=root.image, anchor=tk.NW, tags="IMG")

def resetIdleAnimation():
    idleAnimation = None
    idleAnimationFrame = 0

def idle(scale):
    global frameCount, idleTime, idleAnimation, idleAnimationFrame, nekoSpeed, direction
    idleTime += 1
    if ( idleTime > 10 and random.randint(0,200) == 0 and idleAnimation == None ):
        idleAnimation = random.choice(["sleeping", "scratch"])
    if idleAnimation == "sleeping":
        if (idleAnimationFrame < 8):
            setSprite("tired", 0, scale)
        else:
            setSprite("sleeping", math.floor(idleAnimationFrame / 4), scale);
            if (idleAnimationFrame > 192):
                resetIdleAnimation()
    elif idleAnimation ==  "scratch":
        setSprite("scratch", idleAnimationFrame, scale)
        if (idleAnimationFrame > 9):
            resetIdleAnimation()
    else:
        setSprite("idle", 0, scale);
        return;
    idleAnimationFrame += 1;

def getScale():
    scale=windll.user32.GetDpiForWindow(root.winfo_id())/100
    return round(scale+0.25)

def frame():
    global frameCount, idleTime, idleAnimation, idleAnimationFrame, nekoSpeed, direction, nekoPosX, nekoPosY
    scale = getScale()
    frameCount += 1
    mousePosX = root.winfo_pointerx()/scale
    mousePosY = root.winfo_pointery()/scale
    diffX = nekoPosX - mousePosX
    diffY = nekoPosY - mousePosY
    distance = math.sqrt(math.pow(diffX,2) + math.pow(diffY, 2))
    if(distance == 0): distance = 0.1
    if (distance < nekoSpeed or distance < 48):
        idle(scale)
        return
    idleAnimation = None
    idleAnimationFrame = 0
    if (idleTime > 1):
        setSprite("alert", 0, scale)
        idleTime = min(idleTime, 7)
        idleTime -= 1
        return
    direction = "N" if diffY / distance > 0.5 else "";
    direction += "S" if diffY / distance < -0.5 else "";
    direction += "W" if diffX / distance > 0.5 else "";
    direction += "E" if diffX / distance < -0.5 else "";
    setSprite(direction, frameCount, scale)
    nekoPosX -= (diffX / distance) * nekoSpeed
    nekoPosY -= (diffY / distance) * nekoSpeed
    root.geometry('+{x}+{y}'.format(x=math.floor(nekoPosX*scale),y=math.floor(nekoPosY*scale)))


while True:
    frame()
    messagelock.acquire()
    if message != None:
        scale = getScale()
        setSprite('alert', 1, scale)
        messagebox.showinfo("netkitty", message)
        message = None
    messagelock.release()
    root.update_idletasks()
    root.update()
    time.sleep(100/1000)
