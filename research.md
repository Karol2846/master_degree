# Research Scenarios: Java vs Rust

## 1. CPU-Intensive Workload
**Task:** Generating the Mandelbrot set and saving it to the raw PPM format (due to the lack of built-in image compression support in the Rust standard library).

## 2. I/O-Intensive Workload
**Task:** Sequential processing of a large CSV file (e.g., 5 GB of transaction data).
* Parsing rows,
* Applying a simple filter (searching for the largest transactions),
* Saving matching records to a new file.

## 3. Concurrency and Memory Management
**Task:** An in-memory stream processing engine (IoT simulation).
* Asynchronous reception of millions of events,
* Anomaly filtering and multi-threaded aggregation (moving average).
* **Main goal:** Investigating throughput and comparing latency spikes caused by the Garbage Collector in Java against the determinism of the Ownership model in Rust.