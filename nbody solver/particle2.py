import pyglet
from pyglet.window import key
from pyglet.gl import *
import ratcave as rc
import numpy as np
from pyglet import clock
import math
import time
import random


def get_screen():
    display = pyglet.canvas.Display()
    screen = display.get_default_screen()
    screen_width = screen.width
    screen_height = screen.height
    return screen_width,screen_height


# Disable error checking for increased performance
pyglet.options['debug_gl'] = True

display = pyglet.canvas.get_display()
w,h = get_screen()
config = pyglet.gl.Config(alpha_size=8,sample_buffers=1, samples=16)
window = pyglet.window.Window(config=config,height = h , width = w, resizable = True) #,style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
window.set_fullscreen(True)
glClear(GL_COLOR_BUFFER_BIT)

#glViewport(-100,100,w,h)
#glMatrixMode(GL_PROJECTION)
#glTranslatef(w/2,h/2,0)
glLoadIdentity()
#gluPerspective(35, w/h, 0.1, 100) # fov = 90 degrees; [near, far] = [0.1, 1000]



glMatrixMode(GL_MODELVIEW)
batch = pyglet.graphics.Batch()

#glTranslatef(w/2,h/2,-10)




@window.event
def on_draw():
    #window.flip()
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
    def __init__(self,N):
        self.w,self.h = get_screen()
        self.N = N
        self.setcam()
        self.dispersion = 50
        self.primary_colors = [255,255,255,100]
        self.secondary_colors = [0,0,0]
        self.mass_vector = None
        self.mass = None
        self.mass_var = None
        self.center = None
        self.vertex_list = None

        self.size = 0.01
        self.G = 6.67
        self.viscosity = 0
        self.kg = None

        self.pos = None
        self.speed = None
        self.acc = None
        self.force_matrix = None

        self.oldspeed = None
        self.oldpos = None
        self.oldacc = None
        
        self.nbody_solver = True

        self.init_particles()
        self.init_computational()
        self.draw_particles()

    def setcam(self):
        w = self.w
        h = self.h
        glMatrixMode(GL_MODELVIEW)
        glTranslatef(w/2,h/2,0)

    def setspeed(self,speed = 5,var = 10, preferred_direction = [0,0,0]):
        N = self.N
        pd = preferred_direction

        vc_x = np.full(N,pd[0])
        vc_y = np.full(N,pd[1])
        vc_z = np.full(N,pd[2])

        r = np.random.normal(speed,var,size=3*N).reshape(3,N)

        v_x = r[0] + vc_x 
        v_y = r[1] + vc_y 
        v_z = r[2] + vc_z

        speed = np.asarray([v_x,v_y,v_z],dtype = np.float32).reshape((N,3),order="A")

        self.speed = speed

    def init_particles(self,center = [0,0,0],mass=100,mass_var=1):
        sigma = self.dispersion
        N = self.N
        xc = np.full(N,center[0])
        yc = np.full(N,center[1])
        zc = np.full(N,center[2])
        r = np.random.normal(0,sigma,size=3*N).reshape(3,N)
        masslist = np.random.normal(mass,mass_var,size=N)
        p_x = r[0] + xc 
        p_y = r[1] + yc 
        p_z = r[2] + yc 
        pos = np.asarray([p_x,p_y,p_z],dtype = np.float32).reshape((N,3),order="A") #position random of particles
        
        self.mass = mass
        self.mass_var = mass_var
        self.N = N
        self.center = center
        self.pos = pos
        self.mass_vector = masslist
        self.setspeed()
        self.dminG = 100
        
    def init_computational(self):
        G = self.G
        m = self.mass_vector
        N = self.N
        vi = self.viscosity
        
        acc = np.zeros((N,3))
        speed = np.zeros((N,3))
        zeros = np.zeros((N,3))
        oldacc = np.zeros((N,3))

        
        K = np.zeros((N,N))
        Fg = np.zeros((N,N,3))
        self.force_matrix = Fg
        for i in range(0,N):
            for j in range(0,N):
                K[i,j] = G * m[i] * m[j]
        self.kg = np.asarray(K) 

        self.zeros = zeros
        
        
        self.acc = acc
        self.oldacc = oldacc
        self.speed = speed
        self.Dmin_full = np.full((N,3),100)
        self.viscosity_factor = (1-vi)/(1-vi+0.001)

    def particles_color(self,primary_rgba ,secondary_rgb = [255,255,255]):
        RGBA_P = primary_rgba
        RGBA_S = secondary_rgb
        self.primary_colors = RGBA_P
        self.secondary_colors = RGBA_S

    def draw_particles(self):
        N = self.N
        vertex = self.pos[:,0:2].reshape((2*N),order="F")
        p_col = self.primary_colors
        s_col = self.secondary_colors

        vertex_list = batch.add(N, pyglet.gl.GL_POINTS,None,
                        ('v2f/dynamic', vertex),
                        ('c4B/dynamic', p_col * N),
                        ('s3B', s_col * N)
                        )
        glPointSize(self.size)
        self.vertex_list = vertex_list 



    def compute_fields_acc(self):
        pos = self.pos
        N = self.N
        dmin = self.Dmin_full
        acc = np.zeros(self.acc.shape)
        fields = self.fields
        for field in fields:
            center = field[0]
            rs = field[1]

            distance = center-pos
            den = np.absolute(np.sum(np.power(distance,2)) + dmin)
            a = 1000* rs * np.divide(distance,den)
            acc += a
        return acc

    def update_position(self,dt):
        N = self.N
        vi = self.viscosity_factor
        acc_fields = self.oldacc
        if self.nbody_solver == True:
            acc_nbody = self.solve_nbody()
        else:
            acc_nbody = self.oldacc
            
        self.acc = acc_nbody + acc_fields
        self.speed =  vi * ( self.acc * dt + self.speed)
        self.pos += self.speed * dt

    def solve_nbody(self):
        N = self.N
        kg = self.kg
        pos = self.pos
        acc = np.zeros(self.acc.shape)
        m = self.mass_vector
        F = self.force_matrix
        d_min = self.dminG
        for i in range(0,N):
            for j in range(0,i):
                distance = np.subtract(pos[j],pos[i])
                dm = np.sum(np.absolute(np.power(distance,2))) + d_min
                div = np.power(dm,-3/2)
                d_vect = distance * div
                F[i,j] = np.multiply(kg[j,i] , d_vect)
                F[j,i] = -F[i,j] 
                
            F_sum = np.sum(F[i],axis=0)
            acc[i] = (F_sum/m[i])
        return acc
        
    def update_batch(self):
        N = self.N
        pos = self.pos
        
        pos_2 = pos[:,0:2].reshape((2*N),order="F")
        self.vertex_list.vertices = pos_2
        

    def update(self,dt):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        t = time.time()
        self.update_batch()
        self.update_position(dt)
        
        




if __name__ == "__main__":
    pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
    glDepthFunc(GL_LEQUAL)  
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
    
    particles = particles(100)
    particles.size=1


    clock.schedule_interval(particles.update,0.01)

    pyglet.app.run()