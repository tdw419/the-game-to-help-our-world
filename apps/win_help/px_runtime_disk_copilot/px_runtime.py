
import psutil
import wmi
import time
import datetime
import os

DISK_USAGE_THRESHOLD_MBPS = 5
MONITOR_INTERVAL_SECONDS = 5
LOG_FILE = "px_runtime_disk_log.txt"
ZTXT_OUTPUT_FILE = "px_runtime_ztxt_output.txt"

try:
    c = wmi.WMI()
except Exception as e:
    print(f"Error connecting to WMI: {e}. Cannot get detailed service info.")
    c = None

def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def get_process_disk_io():
    disk_io = {}
    for proc in psutil.process_iter(['pid', 'name', 'io_counters']):
        try:
            io_counters = proc.info['io_counters']
            if io_counters:
                disk_io[proc.pid] = io_counters.read_bytes + io_counters.write_bytes
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return disk_io

def get_svchost_services(pid):
    if not c:
        return []
    services = []
    try:
        for service in c.Win32_Service(ProcessId=pid):
            services.append(service.Name)
    except Exception as e:
        log_message(f"Error getting services for PID {pid} via WMI: {e}")
    return services

def write_ztxt_message(message):
    with open(ZTXT_OUTPUT_FILE, "w") as f:
        f.write(message)

def generate_suggestions(culprit_services):
    suggestions = []
    for service_name in culprit_services:
        if "WSearch" in service_name or "SearchFilterHost" in service_name:
            suggestions.append("Consider disabling 'Windows Search' to reduce disk usage.")
        elif "SysMain" in service_name:
            suggestions.append("Consider disabling 'SysMain' (Superfetch) to reduce prefetch load.")
        elif "BITS" in service_name:
            suggestions.append("BITS may be downloading updates. Check Windows Update settings.")
        elif "DoSvc" in service_name:
            suggestions.append("Disable Delivery Optimization in Update settings.")
        elif "DiagTrack" in service_name:
            suggestions.append("Review Diagnostic and Telemetry services in Privacy settings.")
        suggestions.append(f"Research service '{service_name}' for optimization impact.")
    if not culprit_services:
        suggestions.append("General tips: defragment drive, clean temp files, scan for malware.")
    return "\n".join(list(set(suggestions)))

if __name__ == "__main__":
    log_message("Starting PX Runtime Disk Monitor...")
    previous_disk_io = get_process_disk_io()
    time.sleep(MONITOR_INTERVAL_SECONDS)

    try:
        while True:
            current_disk_io = get_process_disk_io()
            high_disk_processes = {}
            for pid, current_bytes in current_disk_io.items():
                if pid in previous_disk_io:
                    bytes_diff = current_bytes - previous_disk_io[pid]
                    mbps = (bytes_diff / (1024 * 1024)) / MONITOR_INTERVAL_SECONDS
                    if mbps >= DISK_USAGE_THRESHOLD_MBPS:
                        try:
                            proc = psutil.Process(pid)
                            process_name = proc.name()
                            high_disk_processes[pid] = {'name': process_name, 'mbps': mbps}
                        except:
                            continue

            culprit_services = set()
            alert_messages = []
            for pid, info in high_disk_processes.items():
                process_name = info['name']
                mbps = info['mbps']
                alert_messages.append(f"Process: {process_name} (PID: {pid}) - Disk I/O: {mbps:.2f} MB/s")
                if process_name.lower() == "svchost.exe":
                    services = get_svchost_services(pid)
                    for svc in services:
                        culprit_services.add(svc)
                    alert_messages.append(f"  Hosted Services: {', '.join(services)}" if services else "  No specific services found.")

            if high_disk_processes:
                log_message("\n--- HIGH DISK USAGE DETECTED ---")
                for msg in alert_messages:
                    log_message(msg)
                suggestions = generate_suggestions(list(culprit_services))
                log_message("\n--- SUGGESTED ACTIONS ---")
                log_message(suggestions)
                write_ztxt_message("PX Runtime Disk Alert!\n" + "\n".join(alert_messages) + "\n\nSUGGESTIONS:\n" + suggestions)
                log_message("-----------------------------------\n")
            else:
                log_message("Disk usage is normal.")
                write_ztxt_message("PX Runtime: Disk usage normal. All clear.")

            previous_disk_io = current_disk_io
            time.sleep(MONITOR_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        log_message("Monitor stopped by user.")
    except Exception as e:
        log_message(f"Unexpected error: {e}")
    finally:
        log_message("Session ended.")
