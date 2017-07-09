"""
This module performs probabilistic model on some network of streets given by
the modified adjacency matrix (with dictionary of length, width, alpha,
orientation).
"""
#from collections import defaultdict
import numpy as np
import scipy.integrate as integrate
import networkx as nx

from source.junction import Junction

class Model(object):
    """docstring for Model."""
    def __init__(self, modified_adjacency):
        self.__modified_adjacency = modified_adjacency
        self.__nodes = len(modified_adjacency)
        self.__graph = nx.from_numpy_matrix(self.__create_adjacency())
        self.__source = None
        self.__distance_from_source = None
        self.__receiver = None
        self.__distance_from_receiver = None

    def __create_adjacency(self):
        """
        This method returns normal adjacency matrix from modified adjacency
        matrix.
        """
        adjacency = np.zeros((self.__nodes, self.__nodes))
        for i in range(self.__nodes):
            for j in range(self.__nodes):
                if self.__modified_adjacency[i][j] != 0:
                    adjacency[i][j] = 1
        return adjacency

    def set_source(self, source, distance_from_source=0):
        """
        This setter method sets source node.
        TODO: input coordinates, find closest node, set node
        """
        self.__source = source
        self.__distance_from_source = distance_from_source

    def set_receiver(self, receiver, distance_from_receiver=0):
        """
        This setter method sets receiver node.
        TODO: input coordinates, find closest node, set node
        """
        self.__receiver = receiver
        self.__distance_from_receiver = distance_from_receiver

    def solve(self, treshold):
        """
        This method is the main method of the class and it solves the wave
        propagation problem. Treshold specifies length additional to the
        shortest path length.
        """
        assert self.__source is not None and self.__receiver is not None
        paths = self.__compute_paths(treshold) # obtain all connecting paths
        power = 0
        error = 0
        for path in paths:
            integrand = self.__walk(path) # obtain functions and breaking points
            (part_power, part_error) = self.__integrate(integrand)
            power += part_power
            error += part_error
        print("==========================================")
        print("Resulting power from node {0} to node {1} is {2} (error {3})".format(
            self.__source, self.__receiver, power, error))
        return power # resulting power flow

    def __compute_paths(self, treshold):
        """
        This private method computes all paths between source and receiver.
        """
        shortest_length = nx.shortest_path_length(
            self.__graph, self.__source, self.__receiver)
        cutoff = shortest_length + treshold
        distances_dictionary = nx.all_pairs_dijkstra_path_length(
            self.__graph)[self.__receiver]
        paths = self.__find_paths(distances_dictionary, self.__source, cutoff+1)
        return paths


    def __find_paths(self, distances_dictionary, element, n):
        """
        This private method implements an algorithm for finding all paths
        between source and receiver of specified length.
        """
        paths = []
        if n > 0:
            for neighbor in self.__graph.neighbors(element):
                for path in self.__find_paths(distances_dictionary, neighbor, n-1):
                    if distances_dictionary[element] < n:
                        paths.append([element]+path)
        if element == self.__receiver:
            paths.append([element])
        return paths

    def __walk(self, path):
        """
        This private method iterates through the path and fills the functions
        and breaking_points arrays at each step.
        """
        functions = []
        rotations = [0]
        breaking_points = set()
        length = len(path)
        rotation = 0
        if length > 1:
            # Fill length of first and second street
            lengths = [self.__modified_adjacency[path[0]][path[1]]["length"]]
            alphas = [self.__modified_adjacency[path[0]][path[1]]["alpha"]]

            for i in range(1, length-1):
                previous = path[i-1]
                current = path[i]
                following = path[i+1]

                widths = self.__rotate(previous, current, following)
                junction = Junction(widths, current)
                functions.append(junction.compute_function())
                rotation = (rotation+junction.correct_orientation())%2
                rotations.append(rotation)
                breaking_points.add(junction.compute_breaking_point())

                # add length and alpha
                lengths.append(self.__modified_adjacency[current][following]["length"])
                alphas.append(self.__modified_adjacency[current][following]["alpha"])

            # Subtract distance from source/receiver
            lengths[0] -= self.__distance_from_source
            lengths[-1] -= self.__distance_from_receiver

            return {
                "path": path,
                "functions": functions,
                "rotations": rotations,
                "breaks": breaking_points,
                "lengths": lengths,
                "alphas": alphas}
        else:
            raise ValueError("Path too short.")

    def __rotate(self, previous, current, following):
        """
        This private method figures out an orientation of the junction and
        provides information on street widths and exiting street.
        """
        orientation = self.__modified_adjacency[current][previous]["orientation"]
        backward = orientation
        right = (orientation+1)%4
        forward = (orientation+2)%4
        left = (orientation+3)%4
        rotated = {"entry": self.__modified_adjacency[current][previous]["width"]}
        for neighbor in self.__graph.neighbors(current):
            if self.__modified_adjacency[current][neighbor]["orientation"] == left:
                rotated["left"] = self.__modified_adjacency[current][neighbor]["width"]
                if following == neighbor:
                    rotated["next"] = "left"
            elif self.__modified_adjacency[current][neighbor]["orientation"] == forward:
                rotated["forward"] = self.__modified_adjacency[current][neighbor]["width"]
                if following == neighbor:
                    rotated["next"] = "forward"
            elif self.__modified_adjacency[current][neighbor]["orientation"] == right:
                rotated["right"] = self.__modified_adjacency[current][neighbor]["width"]
                if following == neighbor:
                    rotated["next"] = "right"
            elif self.__modified_adjacency[current][neighbor]["orientation"] == backward:
                rotated["backward"] = self.__modified_adjacency[current][neighbor]["width"]
                if following == neighbor:
                    rotated["next"] = "backward"
        return rotated

    def __integrate(self, integrand):
        """
        This private method integrates functions with respect to the breaking
        points.
        """
        path = integrand["path"]
        functions = integrand["functions"]
        rotations = integrand["rotations"]
        breaking_points = integrand["breaks"]
        lengths = integrand["lengths"]
        alphas = integrand["alphas"]

        def compose_function(theta):
            complete = 1/np.pi * (1-alphas[0])**(lengths[0]*np.tan(theta))
            for i in range(1, len(path)-1):
                if rotations[i] == 1:
                    complete = complete * (1-alphas[i])**(lengths[i]*np.tan(np.pi/2-theta)) \
                        *functions[i-1](np.pi/2-theta)
                else:
                    complete = complete * (1-alphas[i])**(lengths[i]*np.tan(theta)) \
                        *functions[i-1](theta)
            if rotations[-1] == 1:
                complete = complete * (1-alphas[-1])**(lengths[-1]*np.tan(np.pi/2-theta))
            else:
                complete = complete * (1-alphas[-1])**(lengths[-1]*np.tan(theta))
            return complete

        (integral, error) = integrate.quad(compose_function, 0, np.pi/2)
        print("Contribution from path {0}: {1} (error {2})".format(path, integral, error))
        return (integral, error)
