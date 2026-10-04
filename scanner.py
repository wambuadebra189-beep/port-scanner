import socket
from concurrent.futures import ThreadPoolExecutor

def scan_port(target, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    result = s.connect_ex((target, port))
    if result==0:
        print(f"Port {port} is OPEN")
        try:
            banner = s.recv(1024)
            print(f"Banner: {banner}")
        except socket.error:
            print(" No banner received")
    s.close()

target = input("Enter target IP to scan: ")
start_port = int(input("Enter start port: "))
end_port = int(input("Enter end port: "))

with ThreadPoolExecutor(max_workers=100) as executor:  
    for port in range(start_port, end_port + 1):
        executor.submit(scan_port, target, port)