# Project Report: Python TCP Port Scanner

This report walks through the final code line by line, explaining what each part does and why it's written that way. It also documents the real bugs hit during development, since debugging them was part of actually learning the material.

## Final code

```python
import socket
from concurrent.futures import ThreadPoolExecutor

def scan_port(target, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    result = s.connect_ex((target, port))
    if result == 0:
        print(f"Port {port} is OPEN")
        try:
            banner = s.recv(1024)
            print(f"Banner: {banner}")
        except socket.error:
            print("No banner received")
    s.close()

target = input("Enter target IP to scan: ")
start_port = int(input("Enter start port: "))
end_port = int(input("Enter end port: "))

with ThreadPoolExecutor(max_workers=100) as executor:
    for port in range(start_port, end_port + 1):
        executor.submit(scan_port, target, port)
```

## Line-by-line explanation

### Imports

```python
import socket
```
`socket` is Python's built-in module for network connections. Every TCP/UDP operation goes through it.

```python
from concurrent.futures import ThreadPoolExecutor
```
A higher-level module built on top of `threading`. `ThreadPoolExecutor` manages a fixed-size pool of worker threads — you submit tasks to it and it runs only as many at once as you specify, queueing the rest.

### The `scan_port` function

```python
def scan_port(target, port):
```
Wraps the scanning logic for a single port into a reusable function, so it can be handed off to a thread pool worker. Takes the target IP and the port number as parameters.

```python
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```
Creates a socket object.
- `AF_INET` = use IPv4 (as opposed to `AF_INET6` for IPv6)
- `SOCK_STREAM` = use TCP (as opposed to `SOCK_DGRAM` for UDP)

A fresh socket is created on every call because a socket can only be used for one connection attempt — it can't be reused for a different port.

```python
    s.settimeout(1)
```
If a connection attempt takes longer than 1 second, give up and raise an error instead of hanging. Without this, closed/filtered ports could cause the scanner to freeze indefinitely.

```python
    result = s.connect_ex((target, port))
```
Attempts the connection. `connect_ex()` (vs. plain `connect()`) returns an **error code** instead of throwing an exception on failure — important because we're checking many ports and don't want the program to crash every time one is closed.
- `0` = success, port accepted the connection (open)
- Any non-zero value = failed (closed or filtered)

```python
    if result == 0:
        print(f"Port {port} is OPEN")
```
Only reports a port when it's actually open — printing every closed port would be noise.

```python
        try:
            banner = s.recv(1024)
            print(f"Banner: {banner}")
        except socket.error:
            print("No banner received")
```
Attempts banner grabbing: reads up to 1024 bytes the service sends back after connecting. Some services (FTP, SSH, SMTP) announce themselves immediately. Others (plain HTTP, RPC, SMB) wait for the client to send a request first and won't send anything unprompted — in that case `recv()` raises an error (often another timeout), which is caught so it doesn't crash the whole scan.

```python
    s.close()
```
Closes the socket. Placed **outside** the `if`/`try`/`except` blocks, at the same indentation level as the socket's creation, so it runs every time regardless of outcome — open, closed, banner received, or not. Leaving sockets open wastes system resources and causes real problems at scale.

### Getting input

```python
target = input("Enter target IP to scan: ")
start_port = int(input("Enter start port: "))
end_port = int(input("Enter end port: "))
```
`input()` always returns a string. `target` stays a string (an IP address is used as text). `start_port` and `end_port` are wrapped in `int(...)` because `range()` requires integers, not text.

### Running the scan concurrently

```python
with ThreadPoolExecutor(max_workers=100) as executor:
    for port in range(start_port, end_port + 1):
        executor.submit(scan_port, target, port)
```
- `range(start_port, end_port + 1)` — the `+ 1` is necessary because `range()` stops *before* its end value; without it, the port typed as "end" would never actually be scanned.
- `max_workers=100` — caps concurrency at 100 threads running at once. Without a cap, creating one raw thread per port (tested with up to 65,535) overwhelms the OS.
- `executor.submit(scan_port, target, port)` — queues `scan_port(target, port)` to run on the next available worker thread, without blocking.
- `with ... as executor:` — automatically waits for every submitted task to finish before the program moves on (no manual thread-joining required).

## Development history: bugs hit and fixed

1. **`s.close()` indented inside the `if result == 0` block** — meant the socket only closed when a port was open, leaking a socket for every closed port scanned. Fixed by moving `s.close()` to the function's base indentation level.
2. **Raw `threading.Thread` per port with no cap** — creating ~65,000 threads at once overwhelmed the system when scanning the full port range. Fixed by switching to `ThreadPoolExecutor` with `max_workers=100`.
3. **`printf` used instead of `print`** (twice, in the banner-grabbing `try`/`except`) — Python has no `printf`; calling it raised a `NameError`. Because the error occurred inside a worker thread, it was silently swallowed by the thread pool rather than shown in the terminal, making the bug look like "nothing happened" rather than an obvious crash. Fixed by replacing both calls with `print`.
4. **`s.close()` indented inside the `except socket.error` block** (recurrence of bug #1 in a new location) — meant the socket only closed when no banner was received. Fixed the same way: moved to the function's base indentation.

## Known limitations

- Only performs a TCP **connect** scan (full three-way handshake) — noisier than a SYN scan, which would require raw sockets/`scapy` and elevated privileges.
- Banner grabbing is passive — it only reads data a service sends unprompted. It doesn't send protocol-specific probes (e.g., an HTTP `GET` request), so it won't get a banner from services like plain HTTP or RPC that wait for the client to speak first.
- No input validation — invalid IPs or non-numeric port input will raise unhandled exceptions.
- No scope/permission check before scanning a target.
