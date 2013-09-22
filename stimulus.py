

class Stimulus(object):
    def __init__(self):
        pass


    # basically just iterate through ordered list of layers and...average? their
    # pixel values to make final picture
    # also would be cool to sneakily have output be same as for Layer so can
    # add a Stimulus to a the ordered list if the fancy strikes you :3
    # also steps everything
    pass



class Layer(object):
    def __init__(self, rows, cols, d=(0,0,0,0)):
        # RGBA tuple matrix
        self.A = np.array([[d for c in range(cols)] for r in range(rows)])


    # TODO: add rotation, translation

        

    # 
    # have RGBA tuple matrix and setters/getters???? (no) 
    # have rotation, translation, step
    # so probably need "basic matrix" which is the result of the stimulus,
    # then "modified matrix" or something which is the rotated, translated,
    # and scaled????? (no) version - also consider basic filtering? like just 
    # inverting everything



"""
Stimuli to make:
-grating - can do PsychoPy style and just have repeating bitmap?
           ehh, would be kind of a pain
also what if want to 'jiggle' grating? (i.e. move a random number of steps
in a random direction? Just define another Layer? Or even could have a
"JiggleLayer" which can be passed another layer and just redefines its
step function or something...
-bar?
"""
