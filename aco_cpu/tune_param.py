from ray import tune

search_space = {
    "num_ants": tune.choice([1, 2, 3, 4]),
    #"cycle": tune.choice([50, 100, 150]),
    #"time_limit": tune.choice([300, 600, 900]),  # in seconds
    "rho": tune.uniform(0.1, 0.9),
    "min_pheromone": tune.loguniform(1e-4, 1e-2),
    "contribution": tune.uniform(0.1, 0.5)
}
