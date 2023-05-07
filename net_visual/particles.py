import support
import pyglet
from pyglet.window import key
from pyglet.gl import *
import numpy as np
from pyglet import clock
import math
import time
import random
import multiprocessing as mp
from functools import partial
from Cython.Build import cythonize
import numba 
from numba import jit
import timeit


class node():
    def __init__(self,position,velocity):
        self.position = np.asarray(position,dtype = np.float32)
        self.velocity = np.asarray(velocity,dtype = np.float32)
        self.acc = np.asarray([0,0,0])
        self.size = 0.1
        self.color = np.asarray((255,255,255,255),dtype = np.int)
        self.vertex_list = None
        self.update_vertex()
        self.parent_arcs=[]
    
    def update_vertex(self):
        pos = self.position
        col = self.color
        
        self.vertex_list = batch.add(
                            1,pyglet.gl.GL_POINTS,None,
                            ('v3f/dynamic', (pos)),
                            ('c4B/dynamic', (col))
                            )
        glPointSize(self.size)
    
    def move(self,d_pos):
        self.position += d_pos
        self.vertex_list.vertices = self.position
    
    def set_pos(self,x,y,z,color = None):
        self.pos = x,y,z
        self.vertex_list.vertices = self.pos 
    
    def setcolor(self,r,g,b,a):
        self.color = np.asarray((r,g,b,a),dtype = np.int)
        self.vertex_list.colors = self.color
        
    def spark_node(self):
        pass

    def spark_next(self):
        pass

    def next_step(self,dt):
        pass


class arc():
    def __init__(self,pos_a,pos_b):
        self.pos_a = np.asarray(pos_a,dtype = np.float32)
        self.pos_b = np.asarray(pos_b,dtype = np.float32)
        self.size = 0.1
        self.col_a = np.asarray((255,255,255,255),dtype = np.int)
        self.col_b = np.asarray((255,255,255,255),dtype = np.int)
        self.vertex_list = None
        self.update_vertex()
        self.previus_node = []
        self.next_node = []
        self.vertex_list = None
        self.update_vertex()

    def update_vertex(self):
        pos_a = self.pos_a
        pos_b = self.pos_b
        pos = np.append(pos_a,pos_b)
        col_a = self.col_a
        col_b = self.col_b
        col = np.append(col_a,col_b)

        self.vertex_list = batch.add(
                            2,pyglet.gl.GL_LINE,None,
                            ('v3f/dynamic', (pos)),
                            ('c4B/dynamic', (col))
                            )
        glPointSize(self.size)


    def spark_arc(self):
        pass

    def spark_next(self):
        pass

    def next_step(self,dt):
        pass


class net_nodes():
    def __init__(self,N):
        self.N = N
        self.nodes = []
        self.color = [255,255,255,255]
        self.acc = np.zeros(shape = (N,3), dtype = np.float32)
 
    def set_color(self,r,g,b,a,delta = 0):
        N = self.N
        r_rand = np.random.uniform(r-delta,r+delta,N)
        g_rand = np.random.uniform(g-delta,g+delta,N)
        b_rand = np.random.uniform(b-delta,b+delta,N)
        a_rand = np.random.uniform(a-delta,a+delta,N)
        
        i = 0
        for p in self.nodes:
            p.setcolor(r_rand[i],g_rand[i],b_rand[i],a_rand[i])
            i += 1

    def spike_color(self,a,delta = 20):
        a_rand = np.random.uniform(a-delta,a+delta,self.N)

        i = 0
        for p in self.nodes:
            p.set_alpha(a_rand[i])
            i += 1

    def create_random_cluster(self,x,y,z,sigma):
        nodes = []
        N = self.N
        xrand = np.random.normal(-10,10,N)
        yrand = np.random.normal(-10,10,N)
        zrand = np.random.normal(-10,10,N)

        for i in range(0,N):
            rand = np.asarray([xrand[i],yrand[i],zrand[i]], dtype = np.float32)
            p = node(rand,[0,0,0])
            p.setcolor(255,255,255,200)
            self.nodes.append(p)
        
    def create_arc(self):
        N = len(self.nodes)
        for node in self.nodes:
            for i in range(0,np.random.randint(1000,size = 1)):
                p = np.random.normal(0,len(self.nodes),N)
                twin_node = self.nodes[p]
                pos_a = node.position
                pos_b =twin_node.position
                arc = arc(pos_a,pos_b)
                node.parent_arc.append(arc)

    @staticmethod
    def get_p_pos(node):
        return node.position
    
    def get_pos_list(self):
        p_pos = self.get_p_pos
        part = self.nodes
        return map(p_pos,part)

    def update_nodes_acc(self):
        acc = self.acc

        i = 0
        for p in self.nodes:
            p.acc = acc[i,:]
            i += 1
  
    def next_step(self,dt):
        self.update_nodes_acc()
        
        for p in self.nodes:
            p.next_step(dt)
            
