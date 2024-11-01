from aco_main_operations import *
from aco_main_makespan import *
from get_input import get_user_input

params = get_user_input()

if __name__ == '__main__':
    if params['objective'] == 'operations':
        main_operations()

    if params['objective'] == 'makespan':
        main_makespan()






