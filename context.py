
from node import Node
from rule import Constraint as C, ExecStep as E

class Context(object):
    """ A class for easing manipulations of node assemblies. """
    
    """ NOTES
    NOTE: Potentially Contexts could have init_lists too? And this is what would
          allow you to connect things/construct circuits from a saved string?
          Seems slightly inelegant...also might be harder to 'insert' something
          into node graph?
    TODO: Be nice if could reference names like "a.b.c.d" relative to current
          lvl, or root.a.b.c.d... for absolute. And would throw an error or
          something if refer to non-unique things? or could just select all 
          matching things...
          To do this could probably add some function to make the ncessary 
          constraint with...like parses on '.' and makes sure each 'parent' is
          correct.
    TODO: For the functions that are assumed to take self.focus, could add
          *args for optionally specifying constraints
    TODO: Might be useful to allow something like "get_constraints" and could
          attempt to connect something and would return a set of appropariate 
          constraints...so users could just connect things in GUI and then
          would properly add constraints so things could be copied...
          I think this ^ would be the same as connect(root, root)
    TODO: Also have "global connect" thing where everything is told to connect
          with everything? and presumably only 'correct' connections happen.
    TODO: Add a context version of filter_nodes that takes *args?
    TODO: Would things be easier if even stored rules just as strings, and only
          'evaluate' when you actually needed them? Then probably wouldn't need
          objects for these things at all.
    TODO: consider having all rules added in a single call to add_rule be ANDed
          together in a single constraint, and then every separate call to 
          add_rule is ORed.
    TODO: Having list of batches seems inelegant (also inelegant for 
          initializing in node. Take advantage of dict-ness to never keep track
          of existing batches? (...or batch order...?)
    TODO: Are there potentially multiple connections / serious inefficiency in 
          connect when, say, trying to connect thresh to feedback? Does
          it get all threshes and all feedbacks and try to connect all multiple
          times?
    """


    def __init__(self):
        # NOTE: (selection has been removed removed)
        # root node of everything. Need to store reference?
        self.root  = Node(None, '$name = "root"')
        # the node currently being manipulated -- could make this a list?
        self.focus = self.root
        # for keeping track of batch to assign to, and existing batch names
        #self.batches = ['init', 'interact', 'update'] # ordered!!
        self.init_batches = ['init']
        self.step_batches = ['interact', 'update']
        self.batches = self.init_batches + self.step_batches # TODO: ehhhhhh
        #self.curr_batch = 'init'
    
    def init_simulation(self):
        """ Reinitialize entire graph, starting from root. """
        self.root.reinitialize()

    def step_simulation(self):
        """ Run each batch in order. """
        for batch in self.step_batches:
            for c in self.focus.cg.nodes():
                c.run_batch(batch)
    
    def set_focus(self, *args):
        """ Pass constraints, 'parent', or 'root', and will set focus. """
        # TODO: better way to handle if there are multiple args?
        # TODO: just have little thing to print what current focus is...
        r = list(args)
        short = len(r) == 1
        if short and r[0] == 'parent':
            self.focus = self.focus.get_parent()
        elif short and r[0] == 'root':
            self.focus = self.root
        else:
            f = self.focus.filter_nodes(C(r), subset=self.focus.get_children())
            if len(f) == 1:
                self.focus = f.pop()
            # should consider having both of these simply print warning
            elif len(f) > 1:
                raise Exception("Too many nodes satisfy that constraint!")
            else:
                raise Exception("No nodes satisfy that constraint!")

    def add_node(self, *args):
        """ Make a new node, extra args will be made into initial steps. """
        Node(self.focus, *args) # auto-insertion seems sorta strange, honestly
        # TODO: you should make sure this actually works...

    def remove_node(self):
        pass

    def move_node(self):
        pass

    def copy_node(self, N=1):
        self.focus.copy(N)

    def add_rule(self, dest, *args):
        """ Add rule to node currently in focus. """
        r = list(args)
        if   dest == 'incoming':
            self.focus.in_rules.append(C(r))
        elif dest == 'outgoing':
            self.focus.out_rules.append(C(r))
        elif dest in self.batches:
            self.focus.batch_steps[dest].append(E(r))
            if dest == 'init':
                # TODO: SURE YOU WANT THIS? could just exec addition instead
                # TODO: perhaps move this somewhere else - such that rather
                #       than init'ing everywhere, just check in one place if 
                #       something has been added to init_list and re-init if so
                #       (maybe even just re-init addition)
                self.focus.initialize()
        else:
            raise Exception("Didn't understand rule destination.")


    #def set_batch(self, batch):
    #    """ Set Context's batch to control which batch steps are added to. 
    #        Batch can be a name or number. """
    #    self.batches.add(batch)
    #    self.curr_batch = batch

    def connect(self, source_constraints, target_constraints):
        """ Try to connect all nodes adhering to given lists of constraints. """
        sources = self.root.filter_nodes(C(source_constraints))
        targets = self.root.filter_nodes(C(target_constraints))
        for s in sources:
            for t in targets:
                self.connect_nodes(s, t)

    def connect_nodes(self, source, target):
        """ Connect two nodes (if they want to). """

        # NOTE: probably not taking full advantage of things - ignores any
        # connection rules that aren't in leaves. Could possibly automate
        # graph structure in these connection rules? Could only choose to 'pass
        # down' connection command if didn't know how to handle it at this level
        # NOTE: Sure this should be in Context?
        # NOTE: Hmm, moved away a little from 'hook up little circuit' interface
        #       and this might be more confusing. Should still allow leaves
        #       to be directly connected to each other without either one
        #       explicitly wanting to? (but only if the leaves are what's being 
        #       connected and not their parents)
        # NOTE: Everything here uses global search...
        # TODO: Should totally allow "group connections" (i.e not force 
        #       constraints to uniquely id a node.

        # get leaves of source and target
        source_leaves = source.get_leaves()
        target_leaves = target.get_leaves()
        #print source_leaves
        # connect anyone that wants to be connected
        for s in source_leaves:
            for t in target_leaves:
                # note that in each instance you pass an 'other'
                # THINK THIS IS WRONG - shouldn't it be 'all(...)'?
                s_c = any([rule.satisfied_by(s, t) for rule in s.out_rules])
                t_c = any([rule.satisfied_by(t, s) for rule in t.in_rules])
                # TODO: Instead of disjunction, could do conjunction unless
                # either has no rules specified, in which case disjunction? So 
                # basically just connect if all existing rules are satisfied...
                #print 'comparing nodes'
                #print s.name
                #print t.name
                if s_c or t_c:
                    # TODO: make this print node attributes?
                    #print 'connection made!'
                    s.cg.add_edge(s,t)


