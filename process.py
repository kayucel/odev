class Process:
    def __init__(self, pid, arrival, burst, priority=0):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.remaining = burst
        self.priority = priority
        self.waiting_time = 0
        self.turnaround_time = 0
        self.completion_time = 0
        self.start_time = -1
        self.response_time = -1
    
    def __repr__(self):
        return f"Process({self.pid}, arrival={self.arrival}, burst={self.burst})"