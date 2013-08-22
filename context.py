
from node import Node
from rule import Constraint as C, ExecStep as E

class Context(object):
    """ A class for easing manipulations of node assemblies. """
    
    """ NOTES
    NOTE: Probably don't need copy and paste... just 'copy' to copy selection
          into graph?
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
    TODO: Sure self.selection is necessary?
    TODO: Think you should get rid of self.selection. Seems like you can do
          basically the same thing by creating constraints, and less to
          think about that way.
    TODO: For the functions that are assumed to take self.focus, could add
          *args for optionally specifying constraints
    TODO: Might be useful to allow something like "get_constraints" and could
          attempt to connect something and would return a set of appropariate 
          constraints...so users could just connect things in GUI and then
          would properly add constraints so things could be copied...
    TODO: Also have "global connect" thing where everything is told to connect
          with everything? and presumably only 'correct' connections happen.
    TODO: Add a context version of filter_nodes that takes *args?
    TODO: Would things be easier if even stored rules just as strings, and only
          'evaluate' when you actually needed them? Then probably wouldn't need
          objects for these things at all.
    """


    def __init__(self):
        # root node of everything. Need to store reference?
        self.root  = Node(None, '$name = "root"')
        # the node currently being manipulated
        self.focus = self.root
        # for copy, pasting? want this? make 'focus' a list instead?
        self.selection = set()
    
    def reinitialize(self):
        """ Reinitialize entire graph, starting from root. """
        self.root.reinitialize()
    
    def set_focus(self, *args):
        """ Pass constraints, 'parent', or 'root', and will set focus. """
        # TODO: better way to handle if there are multiple args?
        # TODO: should clear selection when changing focus?
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

    #def select(self, constraints):
    #    # ...select things within current focus........maybe
    #    subset = self.focus.get_children()
    #    self.selection = self.focus.filter_nodes(constraints, subset)

    def add_node(self, *args):
        """ Make a new node, extra args will be made into init_steps """
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
        elif dest == 'init':
            self.focus.init_steps.append(E(r))
            self.focus.initialize()
            # TODO: SURE YOU WANT TO DO THIS? could just exec addition instead
            # TODO: perhaps could move this somewhere else - such that rather
            #       than init'ing everywhere, just check in one place if 
            #       something has been added to init_list and re-init if so
            #       (maybe even just re-init addition)
        elif dest == 'update':
            self.focus.update_steps.append(E(r))
        else:
            # just print warning?
            raise Exception("Didn't understand rule destination.")


    #def connect(self, source_constraints, target_constraints):
    #    potential_sources = self.root.filter_nodes(target_constraints)
    #    if len(potential_targets) > 1:
    #        raise Exception('Constraints too vague in connect_to.')
    #    target = potential_targets.pop()
    #    # TODO: is it a problem that connect_to uses self.focus?

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
                print 'comparing nodes'
                print s.name
                print t.name
                if s_c or t_c:
                    # TODO: make print node attributes once...do that
                    print 'connection made!'
                    s.cg.add_edge(s,t)



