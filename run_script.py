import subprocess
import time

def run_script(script_name):
    try:
        subprocess.run(['python', script_name], check=True)
        time.sleep(5)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}:\n{e.stderr}")


scripts = ['greedy_runner.py', 'aco_cpu/aco_main.py', 'greedy_runner_gsaco.py']

for script in scripts:
    run_script(script)