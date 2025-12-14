import sys
import os
from process import Process
from scheduler import Scheduler
from utils import read_csv, create_output_dir, save_results
from logger import Logger
from thread_runner import ThreadRunner

def create_process_objects(process_data):
    processes = []
    for data in process_data:
        process = Process(
            pid=data['pid'],
            arrival=data['arrival'],
            burst=data['burst'],
            priority=data['priority']
        )
        processes.append(process)
    return processes

def run_sequential(scheduler, processes, case_name, output_dir):
    algorithms = [
        ('fcfs', scheduler.fcfs, [processes]),
        ('sjf_nonpreemptive', scheduler.sjf_nonpreemptive, [processes]),
        ('sjf_preemptive', scheduler.sjf_preemptive, [processes]),
        ('round_robin', scheduler.round_robin, [processes, 4]),
        ('priority_nonpreemptive', scheduler.priority_nonpreemptive, [processes]),
        ('priority_preemptive', scheduler.priority_preemptive, [processes])
    ]
    
    results = {}
    
    for alg_name, alg_func, args in algorithms:
        print(f"\n{'='*60}")
        print(f"{alg_name.upper()} çalıştırılıyor...")
        print(f"{'='*60}")
        
        scheduler.context_switches = 0
        
        try:
            alg_result = alg_func(*args)
            
            time_points = [50, 100, 150, 200]
            alg_result['throughput'] = scheduler.calculate_throughput(
                alg_result['processes'], time_points
            )
            
            alg_result['cpu_efficiency'] = scheduler.calculate_cpu_efficiency(
                alg_result['processes'], alg_result['total_time']
            )
            
            save_results(alg_result, alg_name, case_name, output_dir)
            results[alg_name] = alg_result
            
            print(f"✓ {alg_name} başarıyla tamamlandı")
            
        except Exception as e:
            print(f"✗ {alg_name} hatası: {e}")
    
    return results

def run_concurrent(scheduler, processes, case_name, output_dir, logger):
    print(f"\n{'='*60}")
    print(f"EŞ ZAMANLI ÇALIŞTIRMA (BONUS) - {case_name.upper()}")
    print(f"{'='*60}")
    
    runner = ThreadRunner(scheduler, processes, case_name, output_dir)
    
    logger.log("THREAD_RUNNER", case_name, "START", "Tüm algoritmalar eş zamanlı başlatılıyor...")
    
    all_results = runner.run_all_algorithms()
    
    for alg_name, result_data in all_results.items():
        if result_data['success']:
            file_name = alg_name.lower().replace(' ', '_')
            save_results(result_data['results'], file_name, case_name, output_dir)
            logger.log(alg_name, case_name, "SUCCESS", 
                      f"Tamamlandı (süre: {result_data['results']['execution_time']:.3f}s)")
        else:
            logger.log(alg_name, case_name, "ERROR", result_data['error'])
    
    return all_results

def generate_report(results, case_name, concurrent_mode=False):
    report_file = f"docs/{case_name}_report.txt"
    
    os.makedirs("docs", exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"İŞLETİM SİSTEMLERİ - CPU ZAMANLAMA RAPORU\n")
        f.write(f"Durum: {case_name.upper()}\n")
        f.write(f"Mod: {'Eş Zamanlı' if concurrent_mode else 'Sıralı'}\n")
        f.write("="*80 + "\n\n")
        
        f.write("ALGORİTMA KARŞILAŞTIRMASI\n")
        f.write("-"*80 + "\n")
        f.write("Algoritma | Ort. Bekleme | Ort. Tamamlanma | Throughput(T=100) | CPU Verim. | Bağlam Değiş.\n")
        f.write("-"*80 + "\n")
        
        for alg_name, result in results.items():
            if isinstance(result, dict) and 'results' in result:
                alg_data = result['results']
            else:
                alg_data = result
            
            metrics = alg_data['metrics']
            throughput = alg_data['throughput']
            efficiency = alg_data['cpu_efficiency']
            context_switches = alg_data['context_switches']
            
            f.write(f"{alg_name[:15]:15} | "
                   f"{metrics['avg_wait']:12.2f} | "
                   f"{metrics['avg_turnaround']:15.2f} | "
                   f"{throughput.get(100, 0):17} | "
                   f"{efficiency:10.2f}% | "
                   f"{context_switches:13}\n")
        
        f.write("-"*80 + "\n\n")
        
        f.write("ANALİZ VE YORUMLAR\n")
        f.write("-"*80 + "\n")
        f.write("1. Bekleme Süreleri:\n")
        f.write("   - FCFS genellikle en yüksek ortalama bekleme süresine sahiptir.\n")
        f.write("   - SJF (özellikle preemptive) en düşük bekleme sürelerini sağlar.\n")
        f.write("   - Round Robin, adil zaman paylaşımı sağlar ama bekleme süreleri artabilir.\n\n")
        
        f.write("2. Throughput:\n")
        f.write("   - Kısa süreli işler için SJF daha yüksek throughput sağlar.\n")
        f.write("   - Uzun zaman dilimlerinde tüm algoritmalar benzer throughput değerlerine ulaşır.\n\n")
        
        f.write("3. CPU Verimliliği:\n")
        f.write("   - Context switch sayısı az olan algoritmalar daha yüksek verimlilik gösterir.\n")
        f.write("   - Preemptive algoritmalar daha fazla context switch yapar.\n\n")
        
        f.write("4. Bağlam Değiştirme:\n")
        f.write("   - Non-preemptive algoritmalar en az context switch yapar.\n")
        f.write("   - Round Robin ve preemptive algoritmalar en fazla context switch yapar.\n")
    
    print(f"\nRapor oluşturuldu: {report_file}")
    
    generate_html_report(results, case_name, concurrent_mode)

def generate_html_report(results, case_name, concurrent_mode=False):
    html_file = f"docs/{case_name}_report.html"
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write("""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CPU Zamanlama Raporu - """ + case_name + """</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px 15px; text-align: center; border: 1px solid #ddd; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .metric { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .algorithm { margin-bottom: 30px; padding: 20px; background-color: #f9f9f9; border-left: 5px solid #3498db; }
        .comment { background-color: #fffde7; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #f39c12; }
        .success { color: #27ae60; font-weight: bold; }
        .warning { color: #e74c3c; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>İŞLETİM SİSTEMLERİ - CPU ZAMANLAMA RAPORU</h1>
        <div class="metric">
            <p><strong>Durum:</strong> """ + case_name.upper() + """</p>
            <p><strong>Çalışma Modu:</strong> """ + ("Eş Zamanlı (Bonus)" if concurrent_mode else "Sıralı") + """</p>
            <p><strong>Toplam Algoritma Sayısı:</strong> 6</p>
        </div>
        
        <h2>ALGORİTMA KARŞILAŞTIRMASI</h2>
        <table>
            <thead>
                <tr>
                    <th>Algoritma</th>
                    <th>Ort. Bekleme Süresi</th>
                    <th>Ort. Tamamlanma Süresi</th>
                    <th>Throughput (T=100)</th>
                    <th>CPU Verimliliği</th>
                    <th>Bağlam Değiştirme</th>
                </tr>
            </thead>
            <tbody>""")
        
        for alg_name, result in results.items():
            if isinstance(result, dict) and 'results' in result:
                alg_data = result['results']
            else:
                alg_data = result
            
            metrics = alg_data['metrics']
            throughput = alg_data['throughput']
            efficiency = alg_data['cpu_efficiency']
            context_switches = alg_data['context_switches']
            
            f.write(f"""
                <tr>
                    <td><strong>{alg_name}</strong></td>
                    <td>{metrics['avg_wait']:.2f}</td>
                    <td>{metrics['avg_turnaround']:.2f}</td>
                    <td>{throughput.get(100, 0)}</td>
                    <td>{efficiency:.2f}%</td>
                    <td>{context_switches}</td>
                </tr>""")
        
        f.write("""
            </tbody>
        </table>
        
        <div class="comment">
            <h3>ANALİZ VE YORUMLAR</h3>
            <p><strong>1. Bekleme Süreleri:</strong> FCFS algoritması genellikle en yüksek ortalama bekleme süresine sahiptir. SJF algoritmaları (özellikle preemptive versiyonu) en düşük bekleme sürelerini sağlar. Round Robin adil zaman paylaşımı sağlar ancak bekleme süreleri artabilir.</p>
            
            <p><strong>2. Throughput:</strong> Kısa süreli işler için SJF algoritmaları daha yüksek throughput sağlar. Uzun zaman dilimlerinde tüm algoritmalar benzer throughput değerlerine ulaşır.</p>
            
            <p><strong>3. CPU Verimliliği:</strong> Context switch sayısı az olan algoritmalar daha yüksek verimlilik gösterir. Preemptive algoritmalar daha fazla context switch yaptığı için verimlilikleri düşebilir.</p>
            
            <p><strong>4. Bağlam Değiştirme:</strong> Non-preemptive algoritmalar en az context switch yapar. Round Robin ve preemptive algoritmalar en fazla context switch yapar.</p>
        </div>
        
        <h2>DETAYLI SONUÇLAR</h2>""")
        
        for alg_name, result in results.items():
            if isinstance(result, dict) and 'results' in result:
                alg_data = result['results']
                exec_time = alg_data.get('execution_time', 0)
            else:
                alg_data = result
                exec_time = 0
            
            f.write(f"""
        <div class="algorithm">
            <h3>{alg_name.upper()}</h3>
            <p><strong>Çalışma Süresi:</strong> {exec_time:.3f} saniye</p>
            <p><strong>Toplam Süre:</strong> {alg_data['total_time']} birim</p>
            <p><strong>Throughput (T=50):</strong> {alg_data['throughput'].get(50, 0)} süreç</p>
            <p><strong>Throughput (T=100):</strong> {alg_data['throughput'].get(100, 0)} süreç</p>
            <p><strong>Throughput (T=150):</strong> {alg_data['throughput'].get(150, 0)} süreç</p>
            <p><strong>Throughput (T=200):</strong> {alg_data['throughput'].get(200, 0)} süreç</p>
        </div>""")
        
        f.write("""
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #7f8c8d;">
            <p>İstanbul Nişantaşı Üniversitesi - Bilgisayar Mühendisliği Bölümü</p>
            <p>EBLM341 - İşletim Sistemleri Ödevi</p>
            <p>© 2024 CPU Zamanlama Simülasyonu</p>
        </div>
    </div>
</body>
</html>""")
    
    print(f"HTML rapor oluşturuldu: {html_file}")

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python main.py [sequential|concurrent]")
        print("Örnek: python main.py concurrent")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    if mode not in ['sequential', 'concurrent']:
        print("Hata: Mod 'sequential' veya 'concurrent' olmalıdır!")
        sys.exit(1)
    
    concurrent_mode = (mode == 'concurrent')
    
    logger = Logger()
    
    case_files = ['case1', 'case2']
    
    for case_name in case_files:
        print(f"\n{'='*80}")
        print(f"{case_name.upper()} İŞLENİYOR...")
        print(f"{'='*80}")
        
        csv_file = f"data/{case_name}.csv"
        process_data = read_csv(csv_file)
        
        if not process_data:
            print(f"{case_name} için veri bulunamadı!")
            continue
        
        processes = create_process_objects(process_data)
        output_dir = create_output_dir(case_name)
        
        print(f"\n{case_name} için {len(processes)} süreç yüklendi:")
        for p in processes:
            print(f"  {p}")
        
        scheduler = Scheduler()
        
        if concurrent_mode:
            results = run_concurrent(scheduler, processes, case_name, output_dir, logger)
        else:
            results = run_sequential(scheduler, processes, case_name, output_dir)
        
        generate_report(results, case_name, concurrent_mode)
    
    logger.save_logs()
    
    print(f"\n{'='*80}")
    print("TÜM İŞLEMLER TAMAMLANDI!")
    print("Sonuçlar 'outputs/' dizininde")
    print("Raporlar 'docs/' dizininde")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()