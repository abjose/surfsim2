
import numpy as np
import scipy.signal
import matplotlib.pyplot as plt

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
__all__ = ['dist', 'rand', 'rand_centered', 
           'hump', 'biphasic', 'exponential', 'threshold',
           'DoG_weight', 'gauss_weight',
           'verify_single', 'Grid', 
           'SinusoidStim', 'JigglySinusoidStim', 'SquareWaveStim',
           'InvertingSinusoidStim', 'BarStim', 'FullFieldStim',
           'DoG_hump']

def dist(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))

def rand(a=0, b=1):
    # return random float in [a,b)
    return (b-a)*np.random.rand() + a

def rand_centered(c, r):
    # return random float centered on c with radius r
    return 2*abs(r)*np.random.rand() - r + c

def hump(size, a, b, c, d, normalize=False):
    # t*exp(-t) with amplitude A, 
    t = np.arange(size)
    #IRF = (2*(t**2)*np.exp(1.25*-t) - 0.005*(t**6)*np.exp(1*-t))
    IRF = a*(t**b)*np.exp(c*-t**d)
    #plt.plot(IRF)
    #plt.show()
    if normalize:
        return IRF / sum(IRF)
    return IRF

def biphasic(size, A):
    #TODO: define this in terms of humps
    # initalize a biphasic irf of size length and A amplitude
    # for testing: identity irf
    #return np.array([1])
    #t = np.arange(0,16,0.1)
    #print A
    #raw_input()
    t = np.arange(size)
    #IRF = A*(2*(t**2)*np.exp(1.25*-t) - 0.005*(t**6)*np.exp(1*-t))
    IRF = (2*(t**2)*np.exp(1.25*-t) - 0.005*(t**6)*np.exp(1*-t))
    IRF /= sum(IRF)
    IRF *= A
    IRF *= -1
    IRF = IRF[::-1]
    #plt.plot(t,IRF)
    #plt.show()
    # TODO: for debugging could have this plot IRF along with A or something?
    return IRF

def exponential(size):
    # TODO: consider using this to define biphasic
    t = np.arange(size)
    IRF = (1*(t**2)*np.exp(1*-t))
    IRF /= sum(IRF)
    IRF *= -1.
    #plt.plot(t,IRF[::-1])
    #plt.show()
    return IRF[::-1] * 0 # TURNED OFF

def gaussian(size, std):
    g = scipy.signal.gaussian(size*2, std)[size:]
    #plt.plot(g)
    #plt.show()
    return g

def gauss_weight(d=1, max_d=10, size=100, std=15):
    ind = (float(dist)/(max_dist+1)) * size
    return gaussian(size, std)[ind]

def DoG(size, s1, s2):
    g = (gaussian(size*2, s1) - (.5*gaussian(size*2, s2)))[size:]
    #plt.plot(g)
    #plt.show()
    # should normalize?
    return g

def DoG_weight(dist, max_dist, size=100, s1=20, s2=40):
    # need max_dist?
    ind = (float(dist)/(max_dist+1)) * size
    return DoG(size, s1, s2)[ind]

def threshold(array, thresh):
    # threshold passed array...could have more parameters, like what to set 
    # things to when they're below the threshold
    # also, if only adding one value at a time, why not just threshold that 
    # single value?
    a = np.array(array)
    a[a < thresh] = 0
    return a

def delay(vec, t):
    """ Just add t 0s to the beginning of vec so most recent data is from
        a few steps ago. """
    return np.array([0.]*t + vec[:-t])

def verify_single(array):
    # throw an exception if input array has too many lists, otherwise return...
    if len(array) > 1:
        raise Exception("Too many inputs!")
    return array


"""
to handle incoming connections, need:
name of predecessor
relevant IRF
weighting function (then weights will become a list of lists, or maybe tuple of lists)
max connection distance
to make outgoing connections, need:
connection target
....also connection distance
"""


def DoG_hump(grid, IRF, input_attributes, connections):
    """ A DoG + hump unit that also discriminates inputs ... 
        'input_attributes' is (pred name, weight func, max dist). 
        'connecitions' is (name, max dist)"""

    # init
    cell  = 'init\n'
    cell += '$x, $y = '+grid+'.get_next()\n'
    cell += '$irf = '+IRF+'\n'
    cell += '$init_data($output_length)\n'
    # generate unit lists and weights for each input
    for name, w, max_dist in input_attributes:
        n = '$'+name
        preds = 'p for p in $get_predecessors() if p.name == ' #ehhhhh
        cell += n+'_units = ['+preds+'"'+name+'"]\n'
        cell += n+'_dists = [dist((p.x, p.y), ($x, $y)) for p in '+n+'_units]\n'
        cell += n+'_weights=['+w+' d=di) for di in '+n+'_dists]\n'

    # interact
    # get all outputs from all input units, convolve with IRF and multiply by 
    # proper weight based on distance
    cell += 'interact\n'
    cell += '$all_outs = []\n' #HACK. Also, don't really need $
    for name, w, max_dist in input_attributes:
        n = '$'+name
        combo = 'for p,w in zip('+n+'_units, '+n+'_weights)'
        cell += n+'_out = [w*np.convolve(p.get_output(), $irf) '+combo+']\n' #??
        cell += '$all_outs.append('+n+'_out)\n'
    cell += '$temp_data = np.sum($all_outs, 0)\n' #??

    # update
    cell += 'update\n'
    cell += '$set_data($temp_data)\n' # can just update most recent?
    cell += '$clean_data($output_length)\n'

    # make outgoing connections
    for target, dist in connections:
        cell += 'outgoing\n'
        #cell += 'other.name == "'+ target +'"\n'
        # want to verify shared parents?
        cell += 'dist((other.x, other.y), ($x, $y)) < '+ dist +'\n'
    
    #print cell
    #raw_input()
    return cell




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





# TODO: Change name to GratingStim?
class SinusoidStim(object):
    def __init__(self, side, spacing=0.1, f=5, amp=1, step_size=.1):
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

class JigglySinusoidStim(SinusoidStim):
    def __init__(self, side, max_jiggle):
        # every time step move up to (max_jiggle) steps in a random direction
        self.max_jiggle = max_jiggle
        super(JigglySinusoidStim, self).__init__(side)

    def step(self):
        sin = self.func(self.range)
        self.output = np.resize(sin, (self.side, self.side))
        self.steps += self.max_jiggle * (np.random.rand()*2. - 1.)

class InvertingSinusoidStim(SinusoidStim):
    def __init__(self, side, invert_steps):
        # will invert every invert_steps steps
        self.invert_steps = invert_steps
        self.sign = 1
        super(InvertingSinusoidStim, self).__init__(side)
        
    def step(self):
        sin = self.func(self.range)
        if self.steps % self.invert_steps == 0:
            self.sign *= -1
        self.output = np.resize(self.sign*sin, (self.side, self.side))
        self.steps += 1


class SquareWaveStim(object):
    def __init__(self, side, dt):
        self.steps    = 0
        self.side     = side
        self.dt       = dt # half period in integer time ticks
        self.curr_vec = [-1.]*side
        self.output   = None
        # fill array initially
        for i in range(side):
            self.step()

    def step(self):
        self.curr_vec = self.curr_vec[1:] + [self.get_square(self.steps)]
        self.output = np.resize(self.curr_vec, (self.side, self.side))
        self.steps += 1

    def get_square(self, t, t0=0):
        return 0. if ((t-t0)%(2*self.dt)) < self.dt else 1.

    def get_dims(self):
        return (self.side, self.side)


class BarStim(object):
    def __init__(self, side, bar):
        self.steps  = 0
        self.side   = side
        self.bar    = bar
        self.output = np.array([1.]*bar + [-1.]*(side-bar)) # (0,1) vs (-1,1)?
        self.output = np.resize(self.output, (self.side, self.side))
            
    def step(self):
        self.output = np.roll(self.output, 1, 1)

    def get_dims(self):
        return (self.side, self.side)


class FullFieldStim(object):
    def __init__(self, side, f):
        self.steps  = 0
        self.freq   = f
        self.side   = side
        self.output = np.array([1.]*side)
        self.output = np.resize(self.output, (self.side, self.side))
            
    def step(self):
        if self.steps % self.freq == 0:
            self.output = -1*self.output
        self.steps += 1

    def get_dims(self):
        return (self.side, self.side)


if __name__=='__main__':
    #plt.plot(-0.25*gaussian(20,10))
    #plt.show()
    #print DoG(29, 2, 7)
    #print DoG_weight(1,20,50,2.5,15)
    #print DoG_weight(1,5)
    #hump(10, 1, 1, .6, 1)
    print gaussian_weight(2,10)
