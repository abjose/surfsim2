
import networkx as nx
import matplotlib.pyplot as plt
import numpy    as np
import pprint


from utils import * # try to remove...
from rule import ExecStep, Constraint

class Node(object):
    """ A class representing (collections of) filters in circuits. """
    
    """ NOTES 
    NOTE: Not taking enough advantage of hierarchy?
    TODO: Should handle output vector with functions to make it easier to be
          consistent about front and back?
    NOTE: Can use update_steps to do filtering, also to check if something
          has moved and need to move self in response or something...
    TODO: (maybe) add an initialization step that allows something to make 
          a copy of itself? But...without copy wanting to copy itself too.
    NOTE: OUTPUT CONVENTION: end of array (i.e. a[len(a)-1]) is newest
    TODO: Make it so init_steps are both run and stored for later. See if this
          is incredibly obnoxious or anything. Could just re-run all init_steps
          each time a new init_step is added??
    TODO: Put various things that should be put in Utils...into utils.
    TODO: Rather than having *args for __init__, could have **kwargs?
    TODO: Add 'batch steps' argument? eh...
    """

    def __init__(self, parent, *args):
        """ Initialize new object and insert into graphs. 
            Extra args are added to init_steps and executed. """
        # connection and hierarchy graphs
        self.cg = parent.cg if parent != None else nx.DiGraph()
        self.hg = parent.hg if parent != None else nx.DiGraph()
        # insert self into graphs, link to parent in hierarchy
        self.cg.add_node(self)
        if parent != None:
            self.hg.add_edge(parent, self)        
        # procedures for various batches - lists of ExecSteps
        self.batch_steps = dict(init=[], interact=[], update=[]) # better name?
        self.batch_steps['init'] = [ExecStep(list(args))] if args else [] 
        #self.init_steps   = [ExecStep(list(args))] if args else []  run on init
        #self.update_steps = [] # run every iteration
        # rules for incoming and outgoing connections - lists of Constraints
        self.in_rules  = []
        self.out_rules = []
        # run initial steps in case any were included
        self.initialize()

    def __getattr__(self, var):
        # If attribute not found, try getting from parent
        parent = self.get_parent()
        if parent != None:
            return eval('parent.' + str(var))
        return None

    def initialize(self):
        """ Initialize self. """
        print 'INITIALIZING:'
        self.run_batch('init', debug=True)

    def reinitialize(self):
        """ Initialize self and tell children to reinitialize too. """
        # TODO: seems like a strange name...
        self.initialize()
        for c in self.get_children():
            c.reinitialize()

    def add_node(self, node): 
        # keep only in Context?
        # consider allowing just a name?
        # would be better if could just pass a name string, that way when saving
        # things could just have a string...
        pass

    def copy(self, N=1, parent=None):
        """ Make N copies of self. """
        # TODO: check to see if parent doesn't exist / is root?
        # set parent if not provided
        if parent == None:
            parent = self.parent()
        for i in range(N):
            # make a new node with same parent
            n = Node(parent)
        
            # append all of own rules to copy
            n.batch_steps['init']     += self.batch_steps['init']
            n.batch_steps['interact'] += self.batch_steps['interact']
            n.batch_steps['update']   += self.batch_steps['update']
            n.in_rules  += self.in_rules
            n.out_rules += self.out_rules

            # now get all children to copy themselves into self copy
            for child in self.get_children():
                child.copy(parent=n)



    """ GRAPH HELPER FUNCTIONS """

    def remove_self(self):
        self.cg.remove_node(self)
        self.hg.remove_node(self)



    """ HIERARCHY GRAPH HELPER FUNCTIONS """

    def parent(self): return self.get_parent()
    def get_parent(self):
        """ Return this node's parent in the hierarchy graph. """
        parent = self.hg.predecessors(self)
        if len(parent) > 1: raise Exception('Multiple parents?!')
        return parent[0] if len(parent) == 1 else None

    def get_children(self):
        """ Return list of this node's children in the hierarchy graph. """
        # TODO: Feel like this should be slightly different - maybe return
        # ALL children in the hierarchy graph? and then another function can
        # return only one level... note that get_successors is already defined.
        return self.hg.successors(self)

    def get_leaves(self):
        """ Return list of leaves rooted at this node in hierarchy. """
        children = self.get_children()
        #print children
        if not children:
            #print "returning self"
            return [self]
        else:
            #print "not returning self..."
            return [l for c in children for l in c.get_leaves()]



    """ CONNECTION GRAPH HELPER FUNCTIONS """

    def get_predecessors(self):
        return self.get_sources()
    def get_sources(self):
        # get list of nodes to get input from
        return self.cg.predecessors(self)

    def get_successors(self):
        return self.get_targes()
    def get_targets(self):
        # get list of nodes that want input from this node
        # ever use this?
        pass

    def get_inputs(self):
        # get list of output lists from sources
        # TODO: sometimes this recurses all the way back to root...avoid?
        # TODO: make default better...
        # TODO: Is this behavior what you want?!?!?!?
        default = [np.array([0.]*self.kernel_length)]
        inputs  = [p.output for p in self.get_sources() if p.output != None]
        return inputs if inputs != [] else default
    
    #def connect_to(self, node):
        # TODO
        # If...have any connection rules?...then try to connect, and stop if 
        # can't? But otherwise tell all children to try to connect_to node 
        # instead.
        # BUT HOW to ultimately make children connect to other's children?
        # This will stay at the same "level" on one side at all times...
        # should this call connect_from in the other group?
        pass
    #def connect_from(self, node):
    #    pass
    

    def filter_nodes(self, constraint, subset=None):
        """ Given a Constraint and subset, return a satisfying set of Nodes. """
        # TODO: should make this take *args instead?
        # gather all potential nodes
        nodes = subset if subset!=None else self.hg.nodes()
        # apply constraint and return
        #for n in nodes:
        #    print n
        #    print constraint.satisfied_by(n)
        #print "done evaluating"
        return {n for n in nodes if constraint.satisfied_by(n)}



    """ STEP AND BATCH FUNCTIONS """

    #def add_batch(...):

    #def set_batch(...):

    def run_batch(self, batch, debug=False):
        #print '\n\n'
        #print batch
        #print self.batch_steps[batch]
        #print self
        for step in self.batch_steps[batch]:
            #step.execute(self)
            if debug: print '\t', step
            step.init_cmd()
            exec(step.cmd) # uggggly



    """ INPUT/OUTPUT FUNCTIONS """

    def convolve_input(self, ):
        # assumes there are incoming connections and self.irf exists
        # sorta strange to have, but justified because so common?
        # should perhaps make into set of strings instead, and put
        # into 'utils' or wherever sets of do-things strings are put?

        # TODO: HMMMMM, this doesn't neccessarily return a full-sized array...
        # what to do? could pad? 
        # or could store extra input values equal to size of irf?
        # or just do 'same' for now?
        # could 'blend' the filtered and unfiltered vectors...
        input_nodes = self.get_sources()
        #print 'input node output: ', input_nodes[0].output
        #print 'irf: ', self.irf
        if input_nodes == []:
            raise Exception('No incoming connections to convolve!')
        elif len(input_nodes) > 1:
            raise Exception('Too many inputs to convolve!')
        
        return np.convolve(input_nodes[0].output, self.irf, mode='same')
    

    def clean_output(self):
        # make sure output is a numpy array of the right length
        # assumes output and kernel_length exist...
        # NOTE: This should potentially be put into Utils.
        assert len(self.output) >= self.kernel_length
        # take newest slice
        #print 'BEFORE: ', self.output
        self.output = np.array(self.output[-self.kernel_length:])
        #print 'AFTER: ', self.output


    def init_output(self, default=0.):
        """ Given kernel_length, intialize a numpy a numpy array. """
        # assumes kernel_length and IRF exist already!!
        # NOTE: This should potentially be put into Utils.
        k = 0
        if self.irf != None:
            k = self.kernel_length
        self.output = np.array([default]*(self.output_length+k-1))

    #def reset(self, order='pic'):
    #    pass



    """ DISPLAY FUNCTIONS """

    def __str__(self):
        # should just...print all variables 'owned' by this object?
        # TODO: make this way, way better.
        return self.name
        #return pprint.pformat(vars(self))

    def show_hg(self):
        nx.draw(self.hg)
        plt.show()
    def show_cg(self):
        nx.draw(self.cg)
        plt.show()

    def print_children(self):
        """ Print all children in hierarchy graph... """
        for c in self.get_children():
            print c

if __name__=='__main__':
    pass
