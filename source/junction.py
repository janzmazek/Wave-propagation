"""
This module implements some common-type junctions.
"""

import numpy as np

class Junction(object):
    """
    This class of methods instantiates a junction object on which wave
    propagation methods are performed.
    """

    def __init__(self, widths, current):
        self.__junction = None
        self.__define_junction(widths)
        self.__validate_junction(widths, current)

        self.__next = widths["next"] # left, forward, right or backward
        entry = widths["backward"] # width of entry street
        exiting = widths[widths["next"]] # width of exiting street
        self.__ratio = exiting/entry # ratio needed for future computations

        self.__crossing = lambda theta, ratio: max(1-ratio*np.tan(theta), 0) # FC
        self.__turning = lambda theta, ratio: 0.5*min(ratio*np.tan(theta), 1) # FT

    def __define_junction(self, widths):
        """
        This private method defines junction type based on input widths.
        """
        junction_size = len(widths) - 1 # number of intersecting streets
        if junction_size == 1:
            self.__junction = "dead-end"
        elif junction_size == 2:
            self.__junction = "bend"
        elif junction_size == 3:
            if "left" in widths and "right" in widths:
                self.__junction =  "t-junction"
            else:
                self.__junction = "side-street"
        elif junction_size == 4:
            self.__junction =  "crossroads"
        else:
            raise ValueError("No such junction type. (junction {0})".format(current))

    def compute_function(self):
        """
        This method returns lambda function for a given junction based on
        street widths and junction type.
        """
        if self.__junction == "dead-end":
            return lambda theta: 1
        elif self.__junction == "bend":
            if self.__next == "backward":
                return lambda theta: self.__crossing(theta, self.__ratio)
            else:
                return lambda theta: 2*self.__turning(theta, self.__ratio)
        elif self.__junction == "t-junction":
            if self.__next == "backward":
                return lambda theta: self.__crossing(theta, 2*self.__ratio)
            else:
                return lambda theta: self.__turning(theta, 2*self.__ratio)
        elif self.__junction == "side-street":
            if self.__next == "forward":
                return lambda theta: self.__crossing(theta, 0.5*self.__ratio)
            elif self.__next == "backward":
                return lambda theta: 0
            else:
                return lambda theta: 2*self.__turning(theta, 0.5*self.__ratio)
        elif self.__junction == "crossroads":
            if self.__next == "forward":
                return lambda theta: self.__crossing(theta, self.__ratio)
            elif self.__next == "backward":
                return lambda theta: 0
            else:
                return lambda theta: self.__turning(theta, self.__ratio)

    def correct_orientation(self):
        """
        This method returns 0 if the streets doesn't change an orientation or
        1 if it changes the orientation.
        """
        if self.__next == "backward" or self.__next == "forward":
            return 0
        else:
            return 1

    def __validate_junction(self, widths, current):
        """
        This private method validates whether the junction is already
        implemented and raises a ValueError if it is not.
        """
        if self.__junction == "bend":
            pass
        elif self.__junction == "t-junction":
            if not widths["left"] == widths["right"]:
                raise ValueError("This junction is not (yet) implemented! \
Opposite streets must be same width. Modify junction {0}".format(current))
                print("Problematic junction is {0}".format(self.__junction))
        elif self.__junction == "side-street":
            if not widths["backward"] == widths["forward"]:
                raise ValueError("This junction is not (yet) implemented! \
Opposite streets must be same width. Modify junction {0}".format(current))
        elif self.__junction == "crossroads":
            if not widths["backward"] == widths["forward"] or not widths["left"] == widths["right"]:
                raise ValueError("This junction is not (yet) implemented! \
Opposite streets must be same width. Modify junction {0}".format(current))
