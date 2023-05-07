import pygletimport pyglet
from pyglet.window import key
from pyglet.gl import *
import ratcave as rc
import numpy as np
from pyglet import clock
import math
import time
import random

# Disable error checking for increased performance
pyglet.options['debug_gl'] = True

display = pyglet.canvas.get_display()
w = 1920
h = 1080

config = pyglet.gl.Config(alpha_size=8,sample_buffers=1, samples=16)
window = pyglet.window.Window(config=config,height =h , width = w, resizable = True)#,style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
window.set_fullscreen(True)
glClear(GL_COLOR_BUFFER_BIT)
window.flip()
glViewport(0,0,w,h)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(35, 1, 0.1, 100000) # fov = 90 degrees; [near, far] = [0.1, 1000]
batch = pyglet.graphics.Batch()
#glMatrixMode(GL_MODELVIEW)
glTranslatef(0,0,0)


@window.event
def on_draw():
    batch.draw()

@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.A:
        print('The "A" key was pressed.')
    elif symbol == key.LEFT:
        print('The left arrow key was pressed.')
    elif symbol == key.ENTER:
        print('The enter key was pressed.')
    elif symbol == key.ESCAPE:
        pyglet.app.exit()

class particles():
    def __init__(self):
        self.C = []
        self.sigma = []
        self.groups = []
        self.N = []
        self.primary_colors = []
        self.secondary_colors = []
        self.group_geom = []
        self.vertexlists = []
        self.reference = []
        self.vertexmatrix = []
        self.acc = []
        self.pos = []
        self.speed = []
        self.mass = []
        self.rif=[]
        self.G = []
        self.m = 10000
        self.chaos = 0
        self.ki_v = 0.2
        self.kp_v = 0.8
        self.kd_v = 0.3
        self.ki_p = 0.0006
        self.kp_p = 0.005
        self.kd_p = 0.001
        self.gravity = True

    def set_mass(self,mass=10000):
        self.m = mass

    def set_pid_p(self,kp,kd,ki):
        self.kp_p = kp
        self.kd_p = kd
        self.ki_p = ki

    def set_pid_v(self,kp,kd,ki):
        self.kp_v = kp
        self.kd_v = kd
        self.ki_v = ki

    def set_chaos(self,c):
        self.chaos = c

    def setscreen(self,w,h):
        self.width = w
        self.height = h

    def init_particles_group(self,N,sigma,C = [0,0],group_name="group"):

        xc = np.full(N,C[0])
        yc = np.full(N,C[1])
        
        r = np.random.normal(0,sigma,size=2*N).reshape(2,N)

        x = r[0] + xc 
        y = r[1] + yc 
        
        pos = np.asarray([x,y],dtype = np.float32).reshape((2,N),order="A")
        A = np.asarray([x,y],dtype = np.float32).reshape((2*N,1),order="F")

        group_id = len(self.groups)
        if group_name == "group":
            group_name = group_name+str(group_id)
        else:
            pass

        self.N.append(N)
        self.C.append(C)
        self.sigma.append(sigma)
        self.group_id = len(self.groups)
        self.groups.append([group_id,group_name])
        self.group_geom.append(pyglet.gl.GL_POINTS)
        self.primary_colors.append([225,225,225,225])
        self.secondary_colors.append([0,0,0])
        self.vertexmatrix.append(A)
        self.vertexlists.append([])
        self.reference.append([0,0,0])
        self.mass.append(np.full(N,self.m*N))
        self.acc.append(np.zeros(pos.shape))
        self.speed.append(np.random.random(pos.shape))
        self.pos.append(pos)
        self.G.append(10^-27)
        self.rif.append([0,0])
        
    def init_group_color(self,group_id,primary_rgba ,secondary_rgb = [0,0,0]):
        id = group_id

        RGBA_P = primary_rgba
        RGBA_S = secondary_rgb

        self.primary_colors[id] = RGBA_P
        self.secondary_colors[id] = RGBA_S

    def draw_particles(self,group_id,geometric_type = pyglet.gl.GL_POINTS,size = 0.1):
        id = group_id

        self.group_geom[id] = geometric_type

        p_col = self.primary_colors[id]
        s_col = self.secondary_colors[id]

        vertex_list = batch.add(self.N[id], geometric_type ,None,
                        ('v2f/dynamic', self.vertexmatrix[id]),
                        ('c4B/dynamic', p_col * self.N[id]),
                        ('s3B', s_col * self.N[id])
                        )
        glPointSize(size)

        self.vertexlists[id] = vertex_list

    def update_particle_reference(self,sigma,rif=[0,0],id = None):
        

        if id == None:
            for i in range(0,len(self.groups)):
                id = self.get_id(self.groups[i][1])
                C = self.C[id] 
                N = self.N[id]
                c_x = C[0] 
                c_y = C[1] 
                #c_z = C[2] 
                
                rif_x = np.random.normal(c_x,sigma,size=1)+rif[0]
                rif_y = np.random.normal(c_y,sigma,size=1)+rif[1]
                #rif_z = np.random.normal(c_z,sigma,size=1)

                rif = [rif_x,rif_y]#,rif_z]

                rif_x = np.full((1 , N),rif[0],dtype = np.uint16) + np.random.normal(0,sigma/10,(1 , N))
                rif_y = np.full((1 , N),rif[1],dtype = np.uint16) + np.random.normal(0,sigma/10,(1 , N))
                #rif_z = np.full((1 , N),rif[2],dtype = np.uint16)

                R = np.array([rif_x,rif_y],dtype = np.uint16).reshape((2,N),order="A")

                self.reference[id] = R
        else :     
            self.rif[id]=rif   

            C = self.C[id] 
            N = self.N[id]
            c_x = C[0] 
            c_y = C[1] 
            #c_z = C[2] 
             
            rif_x = np.random.normal(c_x,sigma,size=1)+rif[0]
            rif_y = np.random.normal(c_y,sigma,size=1)+rif[1]
            #rif_z = np.random.normal(c_z,sigma,size=1)
            rif = [rif_x,rif_y]#,rif_z]
            rif_x = np.full((1 , N),rif[0],dtype = np.uint16) + np.random.normal(0,sigma/10,(1 , N))
            rif_y = np.full((1 , N),rif[1],dtype = np.uint16) + np.random.normal(0,sigma/10,(1 , N))
            #rif_z = np.full((1 , N),rif[2],dtype = np.uint16)
            R = np.array([rif_x,rif_y],dtype = np.uint16).reshape((2,N),order="A")
            self.reference[id] = R
            
    def get_id(self,group_name):
        for el in self.groups:
            if el[1] == group_name:
                id = el[0] 
                return id
            else:
                pass


    def update_particles_position(self,dt):

        for i in range(0,len(self.groups)):
            id = i
            N = self.N[id]
            pos = self.pos[id]
            speed = self.speed[id]
            mass = self.m
            acc = self.acc
            R = self.reference[id]
            G = self.G[id]
            ki_v = self.ki_v
            kp_v = self.kp_v
            kd_v = self.kd_v  
            ki_p = self.ki_p 
            kp_p = self.kp_p
            kd_p = self.kd_p     
            
        
            if self.gravity == True:
                distance = -(R - pos)  #vettore
                
                div = np.power(distance.sum(axis=0),3) #+ 1 * np.ones(distance.shape)) #- dt * np.ones(distance.sum(axis=0).shape) #1/ quadrato della distanza

                a = np.divide(np.ones(div.shape),div)

                new_acc = G * mass * distance* a 
                
            oldspeed = speed  
          

            speed += (new_acc) * dt 
                
            ev = (np.zeros(speed.shape))-speed
            speed += ki_v * ev * dt + kd_v/dt  + kp_v * ev

            ep = -distance
            pos += speed * dt + kd_p /dt * ep + kp_p * ep +ki_p * dt
                
            self.speed[id] = speed
            self.acc[id] = new_acc
            self.pos[id] = pos 

        
            self.vertexmatrix[id] = pos.reshape((2*N,1),order="F")
            
        

    def update_batch(self):
        for i in range(0,len(self.groups)):
            id = self.get_id(self.groups[i][1])
            self.vertexlists[id].vertices = self.vertexmatrix[id]

    def update_particles(self,dt):
        self.update_batch()
        self.update_particles_position(dt)
        



def update(dt):
    glClear(GL_COLOR_BUFFER_BIT)
    #window.flip()
    p.update_particles(dt)


def change_ref(dt):
    t = time.time()
    for i in range(0,100):
        sigma = p.chaos
        a = np.random.normal(0,sigma/2,1)
        b = np.random.normal(0,sigma/2,1)
        p.update_particle_reference(5*dt,rif=[a,b],id = i)
    

if __name__ == "__main__":
    pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
    glDepthFunc(GL_LEQUAL)  
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST)
    glEnable (GL_LINE_SMOOTH)
    glHint (GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
    
    p=particles()
    p.set_chaos(200)
    p.set_pid_v(0.5,0.6,1)
    p.set_pid_p(0.008,0.009,0.06)
    p.set_mass(100)
    for i in range(0,100):
        p.init_particles_group(1000,sigma=10,C=[w/2,h/2])

    #p.init_particles_group(10000,sigma=10,C=[500,500])
        a = (random.randint(40,120))
        r = (random.randint(190,240))
        g = (random.randint(240,255))
        b = (random.randint(250,255))
        
        p.init_group_color(i,[r,g,b,a],[0,225,225])

    #p.init_group_color("group3",[100,100,100,200],[0,225,225])
        
    
        p.draw_particles(i,GL_POINTS,size = 0.01)
        p.update_particle_reference(0,rif=[0,0],id = i)
    #p.draw_particles("group3",GL_POINTS,size = 2)
 
    #clock.schedule_interval(change_ref, 6)
    clock.schedule_interval(update, 0.01)
    
    pyglet.app.run()
