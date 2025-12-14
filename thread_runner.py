import threading
import time
from queue import Queue

class ThreadRunner:
    def __init__(self, scheduler, processes, case_name, output_dir):
        self.scheduler = scheduler
        self.processes = processes
        self.case_name = case_name
        self.output_dir = output_dir
        self.results_queue = Queue()
        self.threads = []
        
    def run_algorithm_thread(self, algorithm_name, algorithm_func, *args):
        try:
            self.scheduler.context_switches = 0
            
            start_time = time.time()
            results = algorithm_func(*args)
            end_time = time.time()
            
            time_points = [50, 100, 150, 200]
            results['throughput'] = self.scheduler.calculate_throughput(
                results['processes'], time_points
            )
            
            results['cpu_efficiency'] = self.scheduler.calculate_cpu_efficiency(
                results['processes'], results['total_time']
            )
            
            results['execution_time'] = end_time - start_time
            
            self.results_queue.put({
                'algorithm': algorithm_name,
                'results': results,
                'success': True
            })
            
        except Exception as e:
            self.results_queue.put({
                'algorithm': algorithm_name,
                'error': str(e),
                'success': False
            })
    
    def run_all_algorithms(self):
        algorithms = [
            ('FCFS', self.scheduler.fcfs, [self.processes]),
            ('SJF Non-Preemptive', self.scheduler.sjf_nonpreemptive, [self.processes]),
            ('SJF Preemptive', self.scheduler.sjf_preemptive, [self.processes]),
            ('Round Robin', self.scheduler.round_robin, [self.processes, 4]),
            ('Priority Non-Preemptive', self.scheduler.priority_nonpreemptive, [self.processes]),
            ('Priority Preemptive', self.scheduler.priority_preemptive, [self.processes])
        ]
        
        for alg_name, alg_func, args in algorithms:
            thread = threading.Thread(
                target=self.run_algorithm_thread,
                args=(alg_name, alg_func, *args)
            )
            self.threads.append(thread)
            thread.start()
            time.sleep(0.01)
        
        for thread in self.threads:
            thread.join()
        
        all_results = {}
        while not self.results_queue.empty():
            result = self.results_queue.get()
            all_results[result['algorithm']] = result
        
        return all_results