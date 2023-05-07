import numpy as np
import pyglet as pg
import ratcave as rc
from pyglet.image import Animation, AnimationFrame
import random
import math 
from pyglet.window import key
keys = key.KeyStateHandler()

frag_shader = """
 #version 120
 uniform vec3 diffuse;
 void main()
 {
     gl_FragColor = vec4(diffuse, 1.);
 }
 """

vert_shader = """
 #version 120
 attribute vec4 vertexPosition;
 uniform mat4 projection_matrix, view_matrix, model_matrix;

 void main()
 {
     gl_Position = projection_matrix * view_matrix * model_matrix * vertexPosition;
 }
 """

shader = rc.Shader(vert=vert_shader, frag=frag_shader)


# Create Window
window = pg.window.Window(800, 600)


@window.event
def on_resize(width, height):
    scene.camera.aspect = width / float(height)

@window.event
def on_draw():
    with rc.default_shader:
        scene.draw()

def update(dt):
    pass

def set_goal():
    pass

pg.clock.schedule(update)

# Insert filename into WavefrontReader.
obj_filename = rc.resources.obj_primitives
obj_reader = rc.WavefrontReader(obj_filename)

def init_particles(gr,ppg,size,sigma = 1, sparse_readius = 10,source = [0,0,0] ):
    obj_filename = rc.resources.obj_primitives
    obj_reader = rc.WavefrontReader(obj_filename)
    g = 0
    i = 0
    mu = 0
    particles = []
    sp = sparse_readius
    while g != gr:

        ppg = math.ceil(ppg + np.random.uniform(0,sigma,1))
        rs = np.random.normal(size, 0.001, ppg)
        x_pp = np.random.normal(mu, sigma, ppg) + np.random.uniform(-sp,sp,ppg) + source[0]
        y_pp = np.random.normal(mu, sigma, ppg) + np.random.uniform(-sp,sp,ppg) + source[1]
        z_pp = np.random.normal(mu, sigma, ppg) + np.random.uniform(-sp,sp,ppg) + source[2]
        
        while i != ppg :
            p = obj_reader.get_mesh("Cube",scale=rs[i])
            p.position.xyz = (x_pp[i], y_pp[i], z_pp[i])
            particles.append(p)
            i +=1
        g += 1
    
    return particles

group = 10
ppg = 1000
particles = init_particles(10,1000,0.01)

def move_particles(dt):
    for p in particles:
        p.position.y +=  0#dt  # dt is the time between frames
        p.position.x +=  0#dt
        p.position.z +=  0#dt


scene = rc.Scene(meshes=particles)
pg.clock.schedule(move_particles)
# Create Scene


scene.bgColor = 0, 0, 0
scene.camera = rc.Camera(position=(0, 0, -20), rotation=(180, 0, 0),z_near = 1,z_far=10000)
pg.gl.glEnable(pg.gl.GL_DEPTH_TEST)
on_draw()
pg.app.run()
