from smt2020 import SMT2020
from graph import Graph


class Colony():

    def __init__(self, parameters):

        self.smt2020 = SMT2020()
        self.graph = Graph()

        self.smt2020.smt_caller(parameters['instance'], parameters['dataset'], parameters['n'],
                                parameters['state'], parameters['breakdown'], parameters['seed'])

        self.machine_map, self.job_tensor, self.adjacency_matrix, \
        self.machine_matrix, self.availability_matrix, \
        self.availability_time_matrix, self.current_time = self.graph.generate_graph(self.smt2020.jobs,
                                                                  self.smt2020.machines, parameters['pheromone_level'],
                                                                  self.smt2020.availability_matrix,
                                                                  self.smt2020.availability_time_matrix,
                                                                  self.smt2020.current_time)






