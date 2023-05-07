from support import *
from cam import *
from particles import *

@window.event
def on_draw():
    
    window.clear()
    camera.update()
    batch.draw()

def update(dt):
    pass

if __name__ == "__main__":
   
    
    gl_active = gl_begin()
    camera = cam()
    
    clock.schedule_interval(update,0.0167)

    pyglet.app.run()
