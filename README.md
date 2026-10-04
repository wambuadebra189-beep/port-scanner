# Python TCP Port Scanner

A multithreaded TCP port scanner built from scratch in Python using raw sockets — no external scanning libraries (no `nmap`, no `scapy`). Built as a learning project toward a network analyst career path.

## Features

- Scans a user-specified target IP across a user-specified port range
- Uses a `ThreadPoolExecutor` to scan ports concurrently (capped at 100 workers) instead of one at a time
- Reports which ports are open
- Attempts banner grabbing on open ports to identify the service running there

## Requirements

- Python 3.x (no external packages — only the standard library)

## Usage

```bash
python scanner.py
```

You'll be prompted for:

```
Enter target IP to scan: 127.0.0.1
Enter start port: 1
Enter end port: 1000
```

Example output:

```
Port 135 is OPEN
No banner received
Port 445 is OPEN
No banner received
```

## ⚠️ Legal / ethical note

Only scan systems you own or have explicit written permission to scan. Scanning systems you don't control without authorization can be illegal, even if you don't intend harm.

## How it works

See [`REPORT.md`](./REPORT.md) for a full line-by-line explanation of the code, including the bugs hit during development and how they were fixed.

## Possible next steps

- Command-line arguments (`argparse`) instead of interactive `input()`
- Output results to CSV/JSON
- UDP scanning support
- SYN (half-open) scanning via raw sockets
