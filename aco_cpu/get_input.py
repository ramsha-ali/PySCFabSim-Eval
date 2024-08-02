from pathlib import Path

def get_user_input():
    script_dir = Path(__file__).resolve().parent.parent
    default_dataset_name = "datasets/SMT2020_HVLM"
    default_dataset_path = script_dir / default_dataset_name
    #dataset_input = input("Enter new dataset or leave blank to use default (HVLM): ")



    parameters = {
        "seed": None,
        "dataset": default_dataset_path, #(script_dir / f'datasets/{dataset_input}') if dataset_input else default_dataset_path,
        "n": int(1), #int(input("Enter Planning Horizon: ") or 1),
        "time_limit": int(5),
        "cycle": int(1) #int(input("Enter max cycles (default 2): ") or 100),
    }

    parameters['dataset'] = Path(parameters['dataset'])


    return parameters