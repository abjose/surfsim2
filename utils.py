
import numpy as np

"""
Things to add...
- Biphasic irf you can scale
- Gaussian points
- Gaussian irf (and DoG)
- Positioning rules?
- An __all__ list
"""

# does this need to be in a class?
# no...also, this technically isn't necessary.
__all__ = ['dist', 'rand', 'rand_centered', 'biphasic', 'threshold',
           'verify_single', 'Grid', 'SinusoidStim']

def dist(a, b):
    print a
    print b
    print np.linalg.norm(np.array(a) - np.array(b))
    #raw_input()
    return np.linalg.norm(np.array(a) - np.array(b))

def rand(a=0, b=1):
    # return random float in [a,b)
    return (b-a)*np.random.rand() + a

def rand_centered(c, r):
    # return random float centered on c with radius r
    return 2*abs(r)*np.random.rand() - r + c

def biphasic(size, A):
    # initalize a biphasic irf of size length and A amplitude
    # for testing: identity irf
    #return np.array([1])
    #t = np.arange(0,16,0.1)
    #print A
    #raw_input()
    t = np.arange(0,size)
    #IRF = A*(2*(t**2)*np.exp(1.25*-t) - 0.005*(t**6)*np.exp(1*-t))
    IRF = (2*(t**2)*np.exp(1.25*-t) - 0.005*(t**6)*np.exp(1*-t))
    IRF /= sum(IRF)
    IRF *= A
    # TODO: for debugging could have this plot IRF along with A or something?
    return -1*IRF#[::-1]


def threshold(array, thresh):
    # threshold passed array...could have more parameters, like what to set 
    # things to when they're below the threshold
    # also, if only adding one value at a time, why not just threshold that 
    # single value?
    a = np.array(array)
    a[a < thresh] = 0
    return a

def verify_single(array):
    # throw an exception if input array has too many lists, otherwise return...
    if len(array) > 1:
        raise Exception("Too many inputs!")
    return array


class BaseStructure(object):
    
    def __init__(self):
        #self.n = 0  # current node
        pass

    #def get_position(self, n):
    #    # get nth position?
    #    pass
    
    def get_next(self):
        # get next position?
        pass

class Line(BaseStructure):
    
    def __init__(self):
        super(Line, self).__init__()

class Grid(BaseStructure):

    def __init__(self, x0=0, y0=0, dx=1, dy=1, xl=10, yl=10):
        super(Grid, self).__init__()
        # just store an array of positions...
        xs = range(x0, xl, dx)
        ys = range(y0, yl, dy)
        self.positions = [(x,y) for x in xs for y in ys]

    def get_next(self):
        if len(self.positions) > 0:
            return self.positions.pop()
        else:
            raise Exception('Trying to get too many grid points.')



# TODO: Have some kind of stimulus base class?

# SHOULD PROBABLY REDO THIS, COPIED FROM SURFSIM
class SinusoidStim(object):
    #import numpy as np

    def __init__(self, side, spacing=0.1, f=5, amp=1, step_size=.5):
        # On a sidexside size grid with each step spacing apart, insert
        # sin with freq f and amplitude amp. On step, increment by step_size.
        # TODO: add ability to change angle
        self.steps  = 0
        self.side   = side
        self.range  = np.arange(0,self.side*spacing, spacing)
        self.func   = lambda x: amp*np.sin(f*x + step_size*self.steps)
        self.output = None
        self.step()

    def step(self):
        sin = self.func(self.range)
        self.output = np.resize(sin, (self.side, self.side))
        self.steps += 1

    def get_dims(self):
        return (self.side, self.side)

class SquareWaveStim(object):
    pass

class BarStim(object):
    pass
