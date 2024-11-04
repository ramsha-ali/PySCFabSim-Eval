

def create_jobs_format(operations, tool_dict):
    jobs_dict = {}
    for op in operations:
        lot, product, step, tool_group, process_time = op
        if (lot, product, step) not in jobs_dict:
            jobs_dict[(lot, product, step)] = []
        jobs_dict[(lot, product, step)].append((process_time, tool_group))

    unique_jobs = set()
    for job_data in operations:
        lot, product, _, _, _ = job_data[:5]
        unique_jobs.add((lot, product))
    all_jobs = list(unique_jobs)
    tool_group_to_machine_ids = {}
    machine_id_counter = 0
    for tool_group, machine_count in tool_dict.items():
        tool_group_to_machine_ids[tool_group] = list(range(machine_id_counter, machine_id_counter + machine_count))
        machine_id_counter += machine_count

    jobs = []
    for i in all_jobs:
        jobss=[]
        l, p =i
        for lot, tasks in jobs_dict.items():
            _l, _p,_s = lot
            if l==_l and p==_p:
                for process_time, tool_group in tasks:
                    alternatives = [(process_time, machine_id) for machine_id in tool_group_to_machine_ids[tool_group]]
                    jobss.append(alternatives)
        jobs.append(jobss)


    return jobs











