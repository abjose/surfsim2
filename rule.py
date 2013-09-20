
# import utils
from utils import *
import numpy as np

# not entirely sure this is necessary
# could move all 'global search' stuff here


# TODO: should probably have a to_string function for saving? (or __repr__)
# TODO: somehow modify so that can do something like C1 and C2 or C3 rather
#       rather than having a list of constraints for filter_nodes, might 
#       be more clear.
# TOOD: Better way to have 'other' in satisfied_by?
# TODO: could convert ! to utils. ??? or something but what about != and stuff??
#       maybe should do...% or something
#       or just check automatically? somehow
# TODO: consider implementing __call__ to evaluate thing...
# TODO: also maybe have __repr__ for printing original string
# TODO: FREAKIN' ADD PRINT STUFF, MANNNN

class Constraint(object):
    
    def __init__(self, constraint_list):
        # constraint_list is a list of logical statements that all must
        # be true for the constraint to be satisfied.
        self.c = constraint_list
        self.checker = None
        # Note: must call init_check before use of constraints
    
    #def __repr__(self):
    #    return str(self.c)

    def init_check(self):
        # convert constraints to something that can be called in check
        # could get rid of this and just save 'compiled' string
        C = ' and '.join(['('+constraint+')' for constraint in self.c])
        # complete variables
        C = C.replace('$', 'node.')
        self.checker = compile(C, '<string>', 'eval')

    def satisfied_by(self, node, other=None):
        """ Return evaluated constraint (should be a truth value). """
        if self.checker == None:
            # should just try to initialize here?
            self.init_check()
            # TODO: is this a problem? could it possibly need to be init'd when
            #       self.checker != None?
            #raise Exception('Constraint not initialized!')
        result = None
        #print self.c
        # TODO: why, when you print self.c here, are there so many repetitions?
        try: result = eval(self.checker)
        except Exception, e:
            raise Exception("Can't eval " + str(self.c) + ' because ' + str(e))
        return result 

class ExecStep(object):
    # TODO: this is almost identical to Constraint...how to combine/reuse code?
    def __init__(self, init_list):
        self.i = init_list
        self.cmd = None

    # TODO: this would be a good candidate for using kwargs instead of strings?

    def __repr__(self):
        return str(self.i)

    def init_cmd(self):
        I = '\n'.join(self.i)
        #I = I.replace('$', 'node.')
        I = I.replace('$', 'self.')
        self.cmd = compile(I, '<string>', 'exec')
        
    def execute(self, node):
        if self.cmd == None:
            self.init_cmd()
        print '\t', self.i

        try: exec(self.cmd)
        except Exception, e:
            raise Exception("Can't exec " + str(self) + ' because ' + str(e))
        #exec(self.cmd)

#class ConstraintList(object)
# could have as disjunction of constraints...and have nice way of saving or 
# something

#class NodeIndex(object):
