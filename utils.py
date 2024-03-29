import math
import numpy as np
import inspect

import tensorflow as tf
from tensorflow import keras
from Logger import Logger

EPS = 1e-8

def get_flat_gradients(loss_fn, var_list):
    with tf.GradientTape() as t:
        loss = loss_fn()
    grads = t.gradient(loss, var_list, unconnected_gradients=tf.UnconnectedGradients.ZERO)
    #print(grads)
    return tf.concat([tf.reshape(g, [-1]) for g in grads], axis=0)

#USED in Logger, it detects the name of the caller of the function it is called in (skip controls how many levels we go back in the stack trace)
def caller_name(skip=2):
    """Get a name of a caller in the format module.class.method
    
       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.
       
       An empty string is returned if skipped levels exceed stack height
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
      return ''
    parentframe = stack[start][0]    
    
    name = []
    module = inspect.getmodule(parentframe)
    if module:
        name.append(module.__name__)
    if 'self' in parentframe.f_locals:
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append( codename ) # function or a method
    del parentframe
    return ".".join(name)

def print_debug(obj=None,debug=True,*strings):
    if not debug: return
    if obj!=None and hasattr(obj,"debug"):
        if obj.debug: 
            print("[",caller_name(),"] ", end="")
            for s in strings:
                print(str(s), end="")
            print()
    else:
        print("[",caller_name(),"]: ", end="")
        for s in strings:
            print(str(s), end="")
        print()

def log(*strings, writeToFile=False, debug_channel="Generic", skip_stack_levels=2, logger=None):
    strings = [str(s) for s in strings]
    if logger!=None:
        logger.print(strings, writeToFile=writeToFile, debug_channel=debug_channel, skip_stack_levels=skip_stack_levels)
