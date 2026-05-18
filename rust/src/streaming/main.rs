mod histogram;
mod read;
mod state;

use std::collections::HashMap;
use std::path::Path;
use std::time::Instant;

const EVENTS_PATH: &str = "output/scenario4_events.bin";
const LATENCY_OUTPUT: &str = "output/scenario4_latency_rust.json";
const WARMUP: u32 = 32;
const K: f64 = 3.0;

fn main() -> std::io::Result<()> {
    let mut state: HashMap<u32, state::SensorState> = HashMap::new();
    let mut hist = histogram::Histogram::new();
    let mut anomalies: u64 = 0;
    let mut events: u64 = 0;

    let wall_start = Instant::now();
    let mut reader = read::EventReader::open(EVENTS_PATH)?;
    loop {
        let t0 = Instant::now();
        let event = match reader.read()? {
            Some(e) => e,
            None => break,
        };
        let s = state
            .entry(event.sensor_id)
            .or_insert_with(state::SensorState::new);
        s.add(event.value);
        if s.count >= WARMUP {
            let n = s.count as f64;
            let mean = s.sum / n;
            let var = (s.sum_sq - s.sum * s.sum / n) / n;
            let std = var.max(0.0).sqrt();
            if (event.value - mean).abs() > K * std {
                anomalies += 1;
            }
        }
        let t1 = Instant::now();
        let dt = t1.saturating_duration_since(t0).as_nanos();
        hist.record(dt.min(u64::MAX as u128) as u64);
        events += 1;
    }

    let elapsed = wall_start.elapsed();
    let elapsed_ms = elapsed.as_secs_f64() * 1000.0;
    let throughput = events as f64 / elapsed.as_secs_f64();

    println!(
        "events={} anomalies={} elapsed_ms={:.2} throughput={:.0}/s",
        events, anomalies, elapsed_ms, throughput
    );
    println!(
        "latency p50={:.2}us p95={:.2}us p99={:.2}us max={:.2}us",
        hist.percentile(50.0) as f64 / 1000.0,
        hist.percentile(95.0) as f64 / 1000.0,
        hist.percentile(99.0) as f64 / 1000.0,
        hist.max_ns as f64 / 1000.0,
    );

    hist.dump_json(Path::new(LATENCY_OUTPUT))?;
    Ok(())
}
