import json
from datetime import datetime

class Logger:
    def __init__(self):
        self.logs = []
        self.start_time = datetime.now()
    
    def log(self, algorithm, case, status, message=""):
        log_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'algorithm': algorithm,
            'case': case,
            'status': status,
            'message': message
        }
        
        self.logs.append(log_entry)
        
        status_color = {
            'START': '\033[94m',
            'SUCCESS': '\033[92m',
            'ERROR': '\033[91m',
            'INFO': '\033[93m'
        }.get(status, '\033[0m')
        
        reset_color = '\033[0m'
        print(f"{status_color}[{status}] {algorithm} - {case}: {message}{reset_color}")
    
    def save_logs(self, filename="execution_log.json"):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'start_time': self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                'end_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'duration': str(datetime.now() - self.start_time),
                'logs': self.logs
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Loglar kaydedildi: {filename}")