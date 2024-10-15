import logging


def get_schedule(job_matrix, machine_map, sequence, machine_asigned, start_job, end_job):
    #print(machine_map)
    last_step = {4:342, 3:582}
    valid_entries = (job_matrix != -1).all(dim=2) # operations not padded
    valid_jobs = job_matrix[valid_entries]
    #print(sequence)
    #print(machine_asigned)
    lot_product_step = []
    scheduled_lots = {}
    schedule_file = 'schedule_output.txt'
    i = 0
    idx = 1
    try:
        with open(schedule_file, 'w') as file:
            file.write("lot\tproduct\tstep\ttool\tmachine\tstart_time\tend_time\n")
            for op_id in sequence[1:]:
                if i < len(valid_jobs):# and idx > 0:
                    required_lot = valid_jobs[op_id - 1]
                    #print(required_lot)
                    lot = required_lot[0].item()
                    product = required_lot[1].item()
                    step = required_lot[2].item()
                    tool = required_lot[3].item()
                    get_tool = machine_map[tool]
                    #print(tool)
                    #print(get_tool)
                    tool_name = get_tool[0]
                    machine = machine_asigned[idx]
                    #print(tool_name, machine)
                    start_time = start_job[i]
                    end_time = end_job[i]
                    i += 1
                    idx += 1
                    tup = (lot, product, step, tool, machine, start_time, end_time)
                    lot_product_step.append(tup)
                    file.write(f"{lot}\t{product}\t{step}\t{tool_name}\t{machine}\t{start_time}\t{end_time}\n")
                    file.flush()

                    if (lot, product) not in scheduled_lots or scheduled_lots[(lot, product)] < step:
                        scheduled_lots[(lot, product)] = step

        logging.info(f"Data written to {schedule_file} successfully")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


    done_lots = set()
    for lot_prod, step in scheduled_lots.items():
        product = lot_prod[1]
        if product in last_step and step >= last_step[product]:
            done_lots.add(lot_prod)

    print(f"Throughput: {len(done_lots)}")
    print()

