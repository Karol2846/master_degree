package org.master.particles;

import java.io.BufferedWriter;
import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.management.RuntimeMXBean;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

// Preallocated per-step measurements; written only by worker 0, read after join.
final class StepLog {

    private final RuntimeMXBean runtime = ManagementFactory.getRuntimeMXBean();

    final long[] stepStartNs;
    final long[] stepNs;
    final long[] positionsNs;
    final long[] cellsNs;
    final long[] forcesNs;
    final long[] velocitiesNs;

    final int[] energyStep;
    final double[] energyKe;
    final double[] energyPe;
    int energyCount = 0;

    long loopStartNs;
    long t0UptimeMs;

    StepLog(int steps) {
        stepStartNs = new long[steps];
        stepNs = new long[steps];
        positionsNs = new long[steps];
        cellsNs = new long[steps];
        forcesNs = new long[steps];
        velocitiesNs = new long[steps];
        // step 0, every ENERGY_EVERY-th step, and the last step if not already a multiple
        int slots = 1 + steps / Particles.ENERGY_EVERY + (steps % Particles.ENERGY_EVERY == 0 ? 0 : 1);
        energyStep = new int[slots];
        energyKe = new double[slots];
        energyPe = new double[slots];
    }

    void markLoopStart() {
        t0UptimeMs = runtime.getUptime();
        loopStartNs = System.nanoTime();
    }

    // Timestamps: step start, then exit from each of the four barriers.
    void recordStep(int step, long t0, long tA, long tB, long tC, long tD) {
        int k = step - 1;
        stepStartNs[k] = t0 - loopStartNs;
        positionsNs[k] = tA - t0;
        cellsNs[k] = tB - tA;
        forcesNs[k] = tC - tB;
        velocitiesNs[k] = tD - tC;
        stepNs[k] = tD - t0;
    }

    void recordEnergy(int step, double ke, double pe) {
        energyStep[energyCount] = step;
        energyKe[energyCount] = ke;
        energyPe[energyCount] = pe;
        energyCount++;
    }

    long loopNs() {
        int last = stepNs.length - 1;
        return last < 0 ? 0 : stepStartNs[last] + stepNs[last];
    }

    double maxEnergyDrift() {
        double e0 = energyKe[0] + energyPe[0];
        double max = 0.0;
        for (int i = 1; i < energyCount; i++) {
            max = Math.max(max, Math.abs(energyKe[i] + energyPe[i] - e0) / Math.abs(e0));
        }
        return max;
    }

    void writeJson(Path path, int n, int threads, int steps) throws IOException {
        Path parent = path.getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        try (BufferedWriter w = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
            w.write("{\n");
            w.write("  \"lang\": \"" + Particles.LANG + "\",\n");
            w.write("  \"n\": " + n + ",\n");
            w.write("  \"threads\": " + threads + ",\n");
            w.write("  \"steps\": " + steps + ",\n");
            w.write("  \"dt\": " + Particles.DT + ",\n");
            w.write("  \"t0_uptime_ms\": " + t0UptimeMs + ",\n");
            writeArray(w, "  ", "step_start_ns", stepStartNs);
            w.write(",\n");
            writeArray(w, "  ", "step_ns", stepNs);
            w.write(",\n");
            w.write("  \"phase_ns\": {\n");
            writeArray(w, "    ", "positions", positionsNs);
            w.write(",\n");
            writeArray(w, "    ", "cells", cellsNs);
            w.write(",\n");
            writeArray(w, "    ", "forces", forcesNs);
            w.write(",\n");
            writeArray(w, "    ", "velocities", velocitiesNs);
            w.write("\n  },\n");
            w.write("  \"energy\": [\n");
            for (int i = 0; i < energyCount; i++) {
                double ke = energyKe[i];
                double pe = energyPe[i];
                w.write("    {\"step\": " + energyStep[i] + ", \"ke\": " + ke + ", \"pe\": " + pe
                        + ", \"total\": " + (ke + pe) + "}");
                w.write(i + 1 < energyCount ? ",\n" : "\n");
            }
            w.write("  ]\n");
            w.write("}\n");
        }
    }

    private static void writeArray(BufferedWriter w, String indent, String name, long[] values) throws IOException {
        w.write(indent + "\"" + name + "\": [");
        for (int i = 0; i < values.length; i++) {
            if (i > 0) {
                w.write(", ");
            }
            w.write(Long.toString(values[i]));
        }
        w.write("]");
    }
}
