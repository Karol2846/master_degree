package org.master.streaming;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public class LatencyHistogram {
    static final int BUCKETS = 64;
    static final int MAX_SHIFT = 56;

    final long[] buckets = new long[BUCKETS];
    long total = 0;
    long minNs = Long.MAX_VALUE;
    long maxNs = 0;
    long sumNs = 0;

    public void record(long nanos) {
        if (nanos < 0) {
            nanos = 0;
        }
        long scaled = Math.max(1L, nanos / 100L);
        int b = 63 - Long.numberOfLeadingZeros(scaled);
        if (b < 0) {
            b = 0;
        }
        if (b >= BUCKETS) {
            b = BUCKETS - 1;
        }
        buckets[b]++;
        total++;
        if (nanos < minNs) {
            minNs = nanos;
        }
        if (nanos > maxNs) {
            maxNs = nanos;
        }
        sumNs += nanos;
    }

    public long getMaxNs() {
        return maxNs;
    }

    public long getMinNs() {
        return minNs == Long.MAX_VALUE ? 0 : minNs;
    }

    public double getMeanNs() {
        return total == 0 ? 0.0 : (double) sumNs / total;
    }

    public long percentile(double pct) {
        if (total == 0) {
            return 0;
        }
        long target = (long) Math.ceil(total * pct / 100.0);
        long running = 0;
        for (int i = 0; i < BUCKETS; i++) {
            running += buckets[i];
            if (running >= target) {
                return bucketUpperBoundNs(i);
            }
        }
        return maxNs;
    }

    static long bucketLowerBoundNs(int i) {
        if (i >= MAX_SHIFT) {
            return Long.MAX_VALUE;
        }
        return 100L << i;
    }

    static long bucketUpperBoundNs(int i) {
        if (i >= BUCKETS - 1) {
            return Long.MAX_VALUE;
        }
        return bucketLowerBoundNs(i + 1);
    }

    public void dumpJson(Path path) throws IOException {
        Path parent = path.getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        try (BufferedWriter w = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
            w.write("{\n");
            w.write("  \"total_events\": " + total + ",\n");
            w.write("  \"min_ns\": " + getMinNs() + ",\n");
            w.write("  \"max_ns\": " + maxNs + ",\n");
            w.write("  \"mean_ns\": " + getMeanNs() + ",\n");
            w.write("  \"p50_ns\": " + percentile(50) + ",\n");
            w.write("  \"p95_ns\": " + percentile(95) + ",\n");
            w.write("  \"p99_ns\": " + percentile(99) + ",\n");
            w.write("  \"p999_ns\": " + percentile(99.9) + ",\n");
            w.write("  \"buckets\": [");
            for (int i = 0; i < BUCKETS; i++) {
                if (i > 0) {
                    w.write(", ");
                }
                w.write(Long.toString(buckets[i]));
            }
            w.write("],\n");
            w.write("  \"bucket_lower_ns\": [");
            for (int i = 0; i < BUCKETS; i++) {
                if (i > 0) {
                    w.write(", ");
                }
                w.write(Long.toString(bucketLowerBoundNs(i)));
            }
            w.write("]\n");
            w.write("}\n");
        }
    }
}
