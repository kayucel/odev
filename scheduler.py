import copy
from collections import deque

class Scheduler:
    def __init__(self, context_switch_time=0.001):
        self.context_switch_time = context_switch_time
        self.context_switches = 0
    
    def calculate_metrics(self, processes):
        total_wait = sum(p.waiting_time for p in processes)
        total_turnaround = sum(p.turnaround_time for p in processes)
        avg_wait = total_wait / len(processes) if processes else 0
        avg_turnaround = total_turnaround / len(processes) if processes else 0
        max_wait = max(p.waiting_time for p in processes) if processes else 0
        max_turnaround = max(p.turnaround_time for p in processes) if processes else 0
        
        return {
            'avg_wait': avg_wait,
            'avg_turnaround': avg_turnaround,
            'max_wait': max_wait,
            'max_turnaround': max_turnaround,
            'total_wait': total_wait,
            'total_turnaround': total_turnaround
        }
    
    def calculate_throughput(self, processes, time_points):
        throughput = {}
        for T in time_points:
            completed = sum(1 for p in processes if p.completion_time <= T)
            throughput[T] = completed
        return throughput
    
    def calculate_cpu_efficiency(self, processes, total_time):
        total_burst = sum(p.burst for p in processes)
        total_context_time = self.context_switches * self.context_switch_time
        efficiency = total_burst / (total_time + total_context_time) if total_time > 0 else 0
        return efficiency * 100
    
    def fcfs(self, processes):
        proc_copy = copy.deepcopy(processes)
        proc_copy.sort(key=lambda x: x.arrival)
        
        time_table = []
        current_time = 0
        
        for process in proc_copy:
            if current_time < process.arrival:
                time_table.append((current_time, "IDLE", process.arrival - current_time))
                current_time = process.arrival
            
            process.start_time = current_time
            time_table.append((current_time, process.pid, process.burst))
            
            process.completion_time = current_time + process.burst
            process.turnaround_time = process.completion_time - process.arrival
            process.waiting_time = process.turnaround_time - process.burst
            
            current_time = process.completion_time
            self.context_switches += 1
        
        total_time = current_time
        metrics = self.calculate_metrics(proc_copy)
        
        return {
            'processes': proc_copy,
            'time_table': time_table,
            'metrics': metrics,
            'total_time': total_time,
            'context_switches': self.context_switches
        }
    
    def sjf_nonpreemptive(self, processes):
        proc_copy = copy.deepcopy(processes)
        proc_copy.sort(key=lambda x: x.arrival)
        
        time_table = []
        current_time = 0
        completed = 0
        n = len(proc_copy)
        is_completed = [False] * n
        
        while completed != n:
            idx = -1
            min_burst = float('inf')
            
            for i in range(n):
                if (proc_copy[i].arrival <= current_time and 
                    not is_completed[i] and 
                    proc_copy[i].burst < min_burst):
                    min_burst = proc_copy[i].burst
                    idx = i
            
            if idx == -1:
                next_arrival = min(p.arrival for i, p in enumerate(proc_copy) 
                                  if not is_completed[i])
                idle_time = next_arrival - current_time
                time_table.append((current_time, "IDLE", idle_time))
                current_time = next_arrival
            else:
                process = proc_copy[idx]
                process.start_time = current_time
                time_table.append((current_time, process.pid, process.burst))
                
                process.completion_time = current_time + process.burst
                process.turnaround_time = process.completion_time - process.arrival
                process.waiting_time = process.turnaround_time - process.burst
                
                current_time = process.completion_time
                is_completed[idx] = True
                completed += 1
                self.context_switches += 1
        
        total_time = current_time
        metrics = self.calculate_metrics(proc_copy)
        
        return {
            'processes': proc_copy,
            'time_table': time_table,
            'metrics': metrics,
            'total_time': total_time,
            'context_switches': self.context_switches
        }
    
    def sjf_preemptive(self, processes):
        proc_copy = copy.deepcopy(processes)
        proc_copy.sort(key=lambda x: x.arrival)
        
        n = len(proc_copy)
        remaining_time = [p.burst for p in proc_copy]
        time_table = []
        current_time = 0
        completed = 0
        prev = -1
        
        while completed != n:
            idx = -1
            min_remaining = float('inf')
            
            for i in range(n):
                if (proc_copy[i].arrival <= current_time and 
                    remaining_time[i] > 0 and 
                    remaining_time[i] < min_remaining):
                    min_remaining = remaining_time[i]
                    idx = i
            
            if idx == -1:
                next_arrival = min(p.arrival for i, p in enumerate(proc_copy) 
                                  if remaining_time[i] > 0)
                idle_time = next_arrival - current_time
                if idle_time > 0:
                    time_table.append((current_time, "IDLE", idle_time))
                current_time = next_arrival
                continue
            
            process = proc_copy[idx]
            
            if process.response_time == -1:
                process.response_time = current_time - process.arrival
            
            if prev != idx and prev != -1:
                self.context_switches += 1
            
            next_event = current_time + 1
            for i in range(n):
                if (proc_copy[i].arrival > current_time and 
                    proc_copy[i].arrival < next_event and 
                    i != idx):
                    next_event = proc_copy[i].arrival
            
            execution_time = min(remaining_time[idx], next_event - current_time)
            
            if execution_time > 0:
                time_table.append((current_time, process.pid, execution_time))
                remaining_time[idx] -= execution_time
                current_time += execution_time
            
            if remaining_time[idx] == 0:
                process.completion_time = current_time
                process.turnaround_time = process.completion_time - process.arrival
                process.waiting_time = process.turnaround_time - process.burst
                completed += 1
            
            prev = idx
        
        self.context_switches += 1
        
        total_time = current_time
        metrics = self.calculate_metrics(proc_copy)
        
        return {
            'processes': proc_copy,
            'time_table': time_table,
            'metrics': metrics,
            'total_time': total_time,
            'context_switches': self.context_switches
        }
    
    def round_robin(self, processes, quantum=4):
        proc_copy = copy.deepcopy(processes)
        proc_copy.sort(key=lambda x: x.arrival)
        
        n = len(proc_copy)
        remaining_time = [p.burst for p in proc_copy]
        time_table = []
        current_time = 0
        completed = 0
        queue = deque()
        in_queue = [False] * n
        response_set = [False] * n
        
        for i in range(n):
            if proc_copy[i].arrival <= current_time:
                queue.append(i)
                in_queue[i] = True
        
        while completed != n:
            if not queue:
                next_arrival = float('inf')
                for i in range(n):
                    if remaining_time[i] > 0 and proc_copy[i].arrival < next_arrival:
                        next_arrival = proc_copy[i].arrival
                
                idle_time = next_arrival - current_time
                if idle_time > 0:
                    time_table.append((current_time, "IDLE", idle_time))
                
                current_time = next_arrival
                
                for i in range(n):
                    if (proc_copy[i].arrival <= current_time and 
                        remaining_time[i] > 0 and 
                        not in_queue[i]):
                        queue.append(i)
                        in_queue[i] = True
                
                continue
            
            idx = queue.popleft()
            in_queue[idx] = False
            
            process = proc_copy[idx]
            
            if not response_set[idx]:
                process.response_time = current_time - process.arrival
                response_set[idx] = True
            
            exec_time = min(quantum, remaining_time[idx])
            time_table.append((current_time, process.pid, exec_time))
            
            remaining_time[idx] -= exec_time
            current_time += exec_time
            
            for i in range(n):
                if (proc_copy[i].arrival <= current_time and 
                    remaining_time[i] > 0 and 
                    not in_queue[i] and 
                    i != idx):
                    queue.append(i)
                    in_queue[i] = True
            
            if remaining_time[idx] > 0:
                queue.append(idx)
                in_queue[idx] = True
            else:
                process.completion_time = current_time
                process.turnaround_time = process.completion_time - process.arrival
                process.waiting_time = process.turnaround_time - process.burst
                completed += 1
            
            self.context_switches += 1
        
        total_time = current_time
        metrics = self.calculate_metrics(proc_copy)
        
        return {
            'processes': proc_copy,
            'time_table': time_table,
            'metrics': metrics,
            'total_time': total_time,
            'context_switches': self.context_switches,
            'quantum': quantum
        }
    
    def priority_nonpreemptive(self, processes):
        proc_copy = copy.deepcopy(processes)
        proc_copy.sort(key=lambda x: x.arrival)
        
        time_table = []
        current_time = 0
        completed = 0
        n = len(proc_copy)
        is_completed = [False] * n
        
        while completed != n:
            idx = -1
            highest_priority = float('inf')
            
            for i in range(n):
                if (proc_copy[i].arrival <= current_time and 
                    not is_completed[i] and 
                    proc_copy[i].priority < highest_priority):
                    highest_priority = proc_copy[i].priority
                    idx = i
            
            if idx == -1:
                next_arrival = min(p.arrival for i, p in enumerate(proc_copy) 
                                  if not is_completed[i])
                idle_time = next_arrival - current_time
                time_table.append((current_time, "IDLE", idle_time))
                current_time = next_arrival
            else:
                process = proc_copy[idx]
                process.start_time = current_time
                time_table.append((current_time, process.pid, process.burst))
                
                process.completion_time = current_time + process.burst
                process.turnaround_time = process.completion_time - process.arrival
                process.waiting_time = process.turnaround_time - process.burst
                
                current_time = process.completion_time
                is_completed[idx] = True
                completed += 1
                self.context_switches += 1
        
        total_time = current_time
        metrics = self.calculate_metrics(proc_copy)
        
        return {
            'processes': proc_copy,
            'time_table': time_table,
            'metrics': metrics,
            'total_time': total_time,
            'context_switches': self.context_switches
        }
    
    def priority_preemptive(self, processes):
        proc_copy = copy.deepcopy(processes)
        proc_copy.sort(key=lambda x: x.arrival)
        
        n = len(proc_copy)
        remaining_time = [p.burst for p in proc_copy]
        time_table = []
        current_time = 0
        completed = 0
        prev = -1
        
        while completed != n:
            idx = -1
            highest_priority = float('inf')
            
            for i in range(n):
                if (proc_copy[i].arrival <= current_time and 
                    remaining_time[i] > 0 and 
                    proc_copy[i].priority < highest_priority):
                    highest_priority = proc_copy[i].priority
                    idx = i
            
            if idx == -1:
                next_arrival = min(p.arrival for i, p in enumerate(proc_copy) 
                                  if remaining_time[i] > 0)
                idle_time = next_arrival - current_time
                if idle_time > 0:
                    time_table.append((current_time, "IDLE", idle_time))
                current_time = next_arrival
                continue
            
            process = proc_copy[idx]
            
            if process.response_time == -1:
                process.response_time = current_time - process.arrival
            
            if prev != idx and prev != -1:
                self.context_switches += 1
            
            next_event = current_time + 1
            for i in range(n):
                if (proc_copy[i].arrival > current_time and 
                    proc_copy[i].arrival < next_event and 
                    i != idx and 
                    proc_copy[i].priority < highest_priority):
                    next_event = proc_copy[i].arrival
            
            execution_time = min(remaining_time[idx], next_event - current_time)
            
            if execution_time > 0:
                time_table.append((current_time, process.pid, execution_time))
                remaining_time[idx] -= execution_time
                current_time += execution_time
            
            if remaining_time[idx] == 0:
                process.completion_time = current_time
                process.turnaround_time = process.completion_time - process.arrival
                process.waiting_time = process.turnaround_time - process.burst
                completed += 1
            
            prev = idx
        
        self.context_switches += 1
        
        total_time = current_time
        metrics = self.calculate_metrics(proc_copy)
        
        return {
            'processes': proc_copy,
            'time_table': time_table,
            'metrics': metrics,
            'total_time': total_time,
            'context_switches': self.context_switches
        }