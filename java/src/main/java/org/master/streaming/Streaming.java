package org.master.streaming;

import java.io.IOException;
import java.nio.file.Path;
import java.util.HashMap;

public class Streaming {

    static final String EVENTS_PATH = "output/scenario4_events.bin";
    static final String LATENCY_OUTPUT = "output/scenario4_latency_java.json";
    static final int WARMUP = 32;
    static final double K = 3.0;

    public static void run() throws IOException {
        HashMap<Integer, SensorState> state = new HashMap<>();
        LatencyHistogram hist = new LatencyHistogram();
        long anomalies = 0;
        long events = 0;

        long wallStart = System.nanoTime();
        try (EventReader reader = new EventReader(EVENTS_PATH)) {
            while (true) {
                long t0 = System.nanoTime();
                EventReader.Event event = reader.read();
                if (event == null) {
                    break;
                }
                SensorState s = state.computeIfAbsent(event.sensorId(), k -> new SensorState());
                s.add(event.value());
                if (s.count >= WARMUP) {
                    double mean = s.sum / s.count;
                    double var = (s.sumSq - s.sum * s.sum / s.count) / s.count;
                    double std = Math.sqrt(Math.max(0.0, var));
                    if (Math.abs(event.value() - mean) > K * std) {
                        anomalies++;
                    }
                }
                long t1 = System.nanoTime();
                hist.record(t1 - t0);
                events++;
            }
        }
        long elapsedNs = System.nanoTime() - wallStart;
        double elapsedMs = elapsedNs / 1_000_000.0;
        double throughput = events / (elapsedNs / 1e9);

        System.out.printf(
                "events=%d anomalies=%d elapsed_ms=%.2f throughput=%.0f/s%n",
                events, anomalies, elapsedMs, throughput);
        System.out.printf(
                "latency p50=%.2fus p95=%.2fus p99=%.2fus max=%.2fus%n",
                hist.percentile(50) / 1000.0,
                hist.percentile(95) / 1000.0,
                hist.percentile(99) / 1000.0,
                hist.getMaxNs() / 1000.0);

        hist.dumpJson(Path.of(LATENCY_OUTPUT));
    }
}
