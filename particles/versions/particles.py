import pyglet
from pyglet.window import key
from pyglet.gl import *
import ratcave as rc
import numpy as np
from pyglet import clock



# Disable error checking for increased performance
pyglet.options['debug_gl'] = True

display = pyglet.canvas.get_display()
config = pyglet.gl.Config(alpha_size=8,sample_buffers=1, samples=8)
window = pyglet.window.Window(config=config,height =1000 , width = 1000, resizable = True)#,style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)
window.set_fullscreen(False)
glClear(GL_COLOR_BUFFER_BIT)
window.flip()
glViewport(0,0,500,500)
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
        self.G = []
        self.m = 1000
        
        
        

    def init_particles_group(self,N,sigma,C = [0,0,0],group_name="group"):

        xc = np.full(N,C[0])
        yc = np.full(N,C[1])
        zc = np.full(N,C[2])

        r = np.random.normal(0,sigma,size=3*N).reshape(3,N)

        x = r[0] + xc 
        y = r[1] + yc 
        z = r[2] + zc 

        pos = np.asarray([x,y,z],dtype = np.float32).reshape((3,N),order="A")
        A = np.asarray([x,y,z],dtype = np.float32).reshape((3*N,1),order="F")
        

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
        self.mass.append(self.m*N)
        self.acc.append(np.zeros(pos.shape))
        self.speed.append(10 * np.random.random(pos.shape))
        self.pos.append(pos)
        self.G.append(10^-27)

    def init_group_color(self,group_name,primary_rgba ,secondary_rgb = [0,0,0]):
        id = self.get_id(group_name)

        RGBA_P = primary_rgba
        RGBA_S = secondary_rgb

        self.primary_colors[id] = RGBA_P
        self.secondary_colors[id] = RGBA_S

    def draw_particles(self,group_name,geometric_type = pyglet.gl.GL_POINTS,size = 0.1):
        id = self.get_id(group_name)

        self.group_geom[id] = geometric_type

        p_col = self.primary_colors[id]
        s_col = self.secondary_colors[id]

        vertex_list = batch.add(self.N[id], geometric_type ,None,
                        ('v3f/dynamic', self.vertexmatrix[id]),
                        ('c4B/dynamic', p_col * self.N[id]),
                        ('s3B', s_col * self.N[id])
                        )
        glPointSize(size)

        self.vertexlists[id] = vertex_list

    def update_particle_reference(self,sigma):
        for i in range(0,len(self.groups)):
            id = self.get_id(self.groups[i][1])
            C = self.C[id] 
            N = self.N[id]
            c_x = C[0] 
            c_y = C[1] 
            c_z = C[2] 
            
            rif_x = np.random.normal(c_x,sigma,size=1)
            rif_y = np.random.normal(c_y,sigma,size=1)
            rif_z = np.random.normal(c_z,sigma,size=1)

            rif = [rif_x,rif_y,rif_z]

            rif_x = np.full((1 , N),rif[0],dtype = np.uint16)
            rif_y = np.full((1 , N),rif[1],dtype = np.uint16)
            rif_z = np.full((1 , N),rif[2],dtype = np.uint16)

            R = np.array([rif_x,rif_y,rif_z],dtype = np.uint16).reshape((3,N),order="A")

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
            id = self.get_id(self.groups[i][1])
            N = self.N[id]
            pos = self.pos[id]
            speed = self.speed[id]
            mass = self.m
            acc = self.acc
            R = self.reference[id]
            G = self.G[id]
            
            
            distance = -(R - pos)  #vettore
            
            div = np.power(distance.sum(axis=0),-1) #1/ quadrato della distanza

            a = div*distance*div

            new_acc = G * mass * a #* np.sign(distance)
            
            speed += new_acc/2 * dt/1


            pos += speed/2 * dt/1
            
            self.speed[id] = speed
            self.acc[id] = new_acc
            self.pos[id] = pos
            
            self.vertexmatrix[id] = pos.reshape((3*N,1),order="F")
            

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
    
    

if __name__ == "__main__":
    pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
    #glDepthFunc(GL_LEQUAL)  
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
    #glEnable(GL_DEPTH_TEST)
    glEnable (GL_LINE_SMOOTH)
    glHint (GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
    
    p=particles()
    #p.init_particles_group(100000,sigma=50,C=[500,500,0])
    p.init_particles_group(100000,sigma=10,C=[500,500,0])
    p.init_group_color("group0",[230,230,230,200],[0,225,225])
    p.update_particle_reference(50)
    
    #p.draw_particles("group0",GL_POINTS)
    p.draw_particles("group0",GL_POINTS)
    
    clock.schedule_interval(update, 0.01)
    
    pyglet.app.run()