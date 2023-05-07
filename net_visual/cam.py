from support import *

class cam():
    def __init__(self):
        self.w,self.h = get_screen()
        self.set_perspective()
        self.pos = np.array([0,0, -20])
        self.rot = np.array([0, 0, 1, 0])

    def set_perspective(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(90, self.w/self.h, 0.1, 100)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_pos(self,pos):
        self.pos = np.array(pos)

    def set_rot(self,rot):
        self.rot = np.array(rot)

    def translate(self,dx,dy,dz):
        self.pos += np.array([dx,dy,dz])

    def update(self):
        self.set_perspective()
        pos = self.pos
        rot = self.rot    
        glTranslatef(pos[0],pos[1],pos[2])
        glRotatef(rot[0], rot[1], rot[2], rot[3])
  