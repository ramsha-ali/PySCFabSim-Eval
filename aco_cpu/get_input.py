from pathlib import Path

def get_user_input():
    script_dir = Path(__file__).resolve().parent.parent
    default_dataset_name = "datasets/SMT2020_example_sch"
    default_dataset_path = script_dir / default_dataset_name
    folder = "simulation_state"
    simulation_instance = script_dir / folder
    # dataset_input = input("Enter new dataset or leave blank to use default: ")

    parameters = {
        "seed": [1],
        "instance" : simulation_instance,
        "dataset": default_dataset_path,   # (script_dir / f'../{dataset_input}') if dataset_input else default_dataset_path
        "n": 5,  # max number of steps per lot
        "days": 3600,  # int(input("enter planning days: "))
        "state": "deterministic",  # deterministic/dynamic
        "pheromone_level": int(1),
        "rho": float(0.3),
        "contribution": float(0.5),
        "min_pheromone": float(0.00001),
        "time_limit": 10,  # int(input("enter time limit for scheduler: "))
        "cycle": 1,  # int(input("enter max cycles: "))
        "num_ants": 1,  # int(input("enter number of ants: "))
        "objective": 'makespan' # or operations/makespan
    }

    parameters['dataset'] = Path(parameters['dataset'])
    parameters['instance'] = Path(parameters['instance'])

    return parameters