from pathlib import Path

def get_user_input():
    script_dir = Path(__file__).resolve().parent.parent
    default_dataset_name = "datasets/SMT2020_HVLM"
    default_dataset_path = script_dir / default_dataset_name
    #dataset_input = input("Enter new dataset or leave blank to use default (LVHM): ")


    parameters = {
        "seed": 0,
        "dataset": default_dataset_path, #(script_dir / f'../{dataset_input}') if dataset_input else default_dataset_path,
        "n": 1, #int(input("Enter Planning Horizon: ") or 1),
        "pheromone_level": int(1),
        "rho": float(0.3),
        "contribution": float(0.5),
        "min_pheromone": float(0.00001),
        "time_limit": 1, ##int(input("Enter time limit for the algorithm: ") or 600),
        "cycle": 1, #int(input("Enter max cycles (default 2): ") or 100),
        "num_ants": 1, #int(input("Enter number of ants (default 10): ") or 10)
    }

    parameters['dataset'] = Path(parameters['dataset'])


    return parameters