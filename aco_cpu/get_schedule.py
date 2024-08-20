


def get_schedule(job_matrix, machine_map, sequence, machine_asigned, start_job, end_job):
    valid_entries = (job_matrix != -1).all(dim=2) # operations not padded
    valid_jobs = job_matrix[valid_entries]
    lot_product_step = []

    i = 0
    idx = 1
    with open('schedule_output.txt', 'w') as file:
        # Write the header to the file
        file.write("lot\tproduct\tstep\ttool\tmachine\tstart_time\tend_time\n")

        for op_id in sequence[1:]:
            if i < len(valid_jobs) and idx > 0:
                required_lot = valid_jobs[op_id - 1]
                lot = required_lot[0]
                product = required_lot[1]
                step = required_lot[2]
                tool = required_lot[3]

                get_tool = machine_map[tool]
                tool_name = get_tool[0]
                machine = machine_asigned[idx]

                start_time = start_job[i]
                end_time = end_job[i]
                i += 1
                idx += 1

                tup = (lot, product, step, tool, machine, start_time, end_time)
                lot_product_step.append(tup)

                file.write(f"{lot}\t{product}\t{step}\t{tool_name}\t{machine}\t{start_time}\t{end_time}\n")



    print("Done")
    #for t in lot_product_step:
        #print(f"Lot: {t[0]}, Product: {t[1]}, Step: {t[2]}, Tool: {t[3]}, Machine: {t[4]}, Start_time: {t[5]}, End_time: {t[6]}")




"""

def get_schedule(job_matrix, sequence, machine_asigned, start_job, end_job):
    valid_entries = (job_matrix != -1).all(dim=2) # operations not padded
    valid_jobs = job_matrix[valid_entries]
    lot_product_step = []
    i = 0
    idx = 1
    for op_id in sequence[1:]:
        if i < len(valid_jobs) and idx > 0:
            required_lot = valid_jobs[op_id - 1]
            lot = required_lot[0]
            product = required_lot[1]
            step = required_lot[2]
            tool = required_lot[3]
            machine = machine_asigned[idx]

            start_time = start_job[i]
            end_time = end_job[i]
            i += 1
            idx += 1

            tup = (lot, product, step, tool, machine, start_time, end_time)
            lot_product_step.append(tup)

    for t in lot_product_step:
        print(
            f"Lot: {t[0]}, Product: {t[1]}, Step: {t[2]}, Tool: {t[3]}, Machine: {t[4]}, Start_time: {t[5]}, End_time: {t[6]}")
"""