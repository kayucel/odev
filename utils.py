import csv
import os

def read_csv(file_path):
    processes = []
    
    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                pid = row['PID']
                arrival = int(row['Arrival'])
                burst = int(row['Burst'])
                priority = int(row.get('Priority', 0))
                
                processes.append({
                    'pid': pid,
                    'arrival': arrival,
                    'burst': burst,
                    'priority': priority
                })
    except FileNotFoundError:
        print(f"Hata: {file_path} dosyası bulunamadı!")
        return []
    except KeyError as e:
        print(f"Hata: CSV dosyasında gerekli sütun eksik: {e}")
        return []
    
    return processes

def create_output_dir(case_name):
    dir_path = f"outputs/{case_name}"
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def save_results(results, algorithm_name, case_name, output_dir):
    file_path = f"{output_dir}/{algorithm_name}.txt"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"=== {algorithm_name.upper()} - {case_name.upper()} ===\n\n")
        
        f.write("Zaman Tablosu:\n")
        f.write("-" * 50 + "\n")
        for start, pid, duration in results['time_table']:
            f.write(f"[{start:3}] --- {pid:6} --- [{start+duration:3}]\n")
        f.write("-" * 50 + "\n\n")
        
        metrics = results['metrics']
        f.write("METRİKLER:\n")
        f.write("-" * 50 + "\n")
        f.write(f"Ortalama Bekleme Süresi: {metrics['avg_wait']:.2f}\n")
        f.write(f"Maksimum Bekleme Süresi: {metrics['max_wait']:.2f}\n")
        f.write(f"Ortalama Tamamlanma Süresi: {metrics['avg_turnaround']:.2f}\n")
        f.write(f"Maksimum Tamamlanma Süresi: {metrics['max_turnaround']:.2f}\n")
        f.write(f"Toplam Bekleme Süresi: {metrics['total_wait']:.2f}\n")
        f.write(f"Toplam Tamamlanma Süresi: {metrics['total_turnaround']:.2f}\n")
        f.write("-" * 50 + "\n\n")
        
        time_points = [50, 100, 150, 200]
        throughput = results.get('throughput', {})
        if not throughput:
            from scheduler import Scheduler
            scheduler = Scheduler()
            throughput = scheduler.calculate_throughput(results['processes'], time_points)
        
        f.write("THROUGHPUT:\n")
        f.write("-" * 50 + "\n")
        for T in time_points:
            count = throughput.get(T, 0)
            f.write(f"T={T}: {count} süreç tamamlandı\n")
        f.write("-" * 50 + "\n\n")
        
        efficiency = results.get('cpu_efficiency', 0)
        if efficiency == 0:
            efficiency = scheduler.calculate_cpu_efficiency(
                results['processes'], 
                results['total_time']
            )
        
        f.write("CPU VERİMLİLİĞİ:\n")
        f.write("-" * 50 + "\n")
        f.write(f"Ortalama CPU Verimliliği: {efficiency:.2f}%\n")
        f.write(f"Toplam Bağlam Değiştirme Sayısı: {results['context_switches']}\n")
        f.write("-" * 50 + "\n\n")
        
        f.write("SÜREÇ DETAYLARI:\n")
        f.write("-" * 80 + "\n")
        f.write("PID | Arrival | Burst | Priority | Start | Completion | Turnaround | Waiting\n")
        f.write("-" * 80 + "\n")
        
        for process in sorted(results['processes'], key=lambda x: x.pid):
            f.write(f"{process.pid:3} | "
                   f"{process.arrival:7} | "
                   f"{process.burst:5} | "
                   f"{process.priority:8} | "
                   f"{process.start_time if process.start_time != -1 else 'N/A':5} | "
                   f"{process.completion_time:10} | "
                   f"{process.turnaround_time:10} | "
                   f"{process.waiting_time:7}\n")
        
        f.write("-" * 80 + "\n")
    
    print(f"Sonuçlar kaydedildi: {file_path}")
    return file_path