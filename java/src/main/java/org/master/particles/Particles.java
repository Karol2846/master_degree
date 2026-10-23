package org.master.particles;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Locale;

public class Particles {

    static final double RC = 2.5;
    static final double RC2 = RC * RC;
    static final double DT = 0.005;
    private static final double INV_RC6 = 1.0 / (RC2 * RC2 * RC2);
    // Potential shift 4 (rc^-12 - rc^-6); used only for reported energy, forces are unshifted.
    static final double E_SHIFT = 4.0 * (INV_RC6 * INV_RC6 - INV_RC6);
    static final int ENERGY_EVERY = 10;
    static final String LANG = "java";
    static final String STEPS_OUTPUT = "output/scenario3_steps_java_n%d_p%d.json";
    static final String SNAPSHOT_OUTPUT = "output/scenario3_snapshots_java.xyz";

    static void run(Options opts) throws IOException, InterruptedException {
        ParticleFile.Input input = ParticleFile.read(opts.input());
        Particle[] particles = input.particles();
        CellGrid grid = new CellGrid(input.boxLength());
        StepLog log = new StepLog(opts.steps());

        try (XyzWriter snapshots = opts.snapshotEvery() > 0 ? new XyzWriter(Path.of(SNAPSHOT_OUTPUT)) : null) {
            Simulation sim = new Simulation(
                    particles, grid, opts.threads(), opts.steps(), log, snapshots, opts.snapshotEvery());
            sim.run();
        }

        if (opts.dumpFinal() != null) {
            ParticleFile.writeFinal(opts.dumpFinal(), particles);
        }
        log.writeJson(Path.of(String.format(STEPS_OUTPUT, particles.length, opts.threads())),
                particles.length, opts.threads(), opts.steps());

        System.out.printf(Locale.ROOT,
                "n=%d threads=%d steps=%d loop_ms=%.2f energy_drift=%.3e\n",
                particles.length, opts.threads(), opts.steps(), log.loopNs() / 1_000_000.0, log.maxEnergyDrift());
    }
}
