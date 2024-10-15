from smt2020 import SMT2020
from graph import Graph
from machine_instance import Machine_Instance


class Colony():

    def __init__(self, parameters):
        self.machine_instance = Machine_Instance()
        self.smt2020 = SMT2020()
        self.graph = Graph()

        self.machine_instance.get_machine_instance(parameters['instance'])



        self.smt2020.smt_caller(parameters['instance'], parameters['dataset'], parameters['n'], parameters['state'], parameters['seed'])


        self.machine_map, self.job_tensor, self.adjacency_matrix, \
        self.machine_matrix, self.availability_matrix, \
        self.availability_time_matrix, self.current_time = self.graph.generate_graph(self.smt2020.jobs,
                                                                  self.smt2020.machines, parameters['pheromone_level'],
                                                                  self.machine_instance.availability_matrix,
                                                                  self.machine_instance.availability_time_matrix,
                                                                  self.machine_instance.current_time)






