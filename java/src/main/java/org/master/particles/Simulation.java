package org.master.particles;

import java.io.IOException;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CyclicBarrier;

// P long-lived worker threads synchronised by one CyclicBarrier. Each worker writes only its own
// contiguous block of particles; worker 0 additionally runs the serial cell-list phase and the timing.
final class Simulation {

    private final Particle[] particles;
    private final double boxLength;
    private final double halfBox;
    private final int threads;
    private final int steps;
    private final CellGrid grid;
    private final CyclicBarrier barrier;
    private final StepLog log;
    private final XyzWriter snapshots;
    private final int snapshotEvery;

    // Per-thread partial sums, combined by worker 0 in thread order.
    private final double[] pePartial;
    private final double[] kePartial;
    private final Throwable[] failures;
    // First snapshot write error; written by worker 0 only, rethrown after join.
    private IOException snapshotError;

    Simulation(Particle[] particles, CellGrid grid, int threads, int steps,
               StepLog log, XyzWriter snapshots, int snapshotEvery) {
        this.particles = particles;
        this.boxLength = grid.boxLength;
        this.halfBox = 0.5 * boxLength;
        this.threads = threads;
        this.steps = steps;
        this.grid = grid;
        this.barrier = new CyclicBarrier(threads);
        this.log = log;
        this.snapshots = snapshots;
        this.snapshotEvery = snapshotEvery;
        this.pePartial = new double[threads];
        this.kePartial = new double[threads];
        this.failures = new Throwable[threads];
    }

    void run() throws InterruptedException, IOException {
        Thread[] workers = new Thread[threads];
        for (int t = 0; t < threads; t++) {
            int id = t;
            workers[t] = new Thread(() -> work(id), "particles-worker-" + t);
            workers[t].start();
        }
        for (Thread worker : workers) {
            worker.join();
        }
        // Report the original failure rather than the BrokenBarrierException it caused in other workers.
        Throwable root = null;
        for (Throwable f : failures) {
            if (f != null && (root == null || root instanceof BrokenBarrierException)) {
                root = f;
            }
        }
        if (root != null) {
            throw new IllegalStateException("simulation worker failed", root);
        }
        if (snapshotError != null) {
            throw snapshotError;
        }
    }

    private void work(int t) {
        try {
            loop(t);
        } catch (Throwable e) {
            failures[t] = e;
            // Break the barrier so the remaining workers do not wait forever.
            barrier.reset();
        }
    }

    private void loop(int t) throws InterruptedException, BrokenBarrierException {
        int n = particles.length;
        int from = t * n / threads;
        int to = (t + 1) * n / threads;
        boolean leader = t == 0;

        // Initialisation (outside the measured loop): cell list, initial forces, step-0 energy.
        if (leader) {
            grid.rebuild(particles);
            snapshot(0);
        }
        barrier.await();
        pePartial[t] = computeForces(from, to);
        kePartial[t] = kineticEnergy(from, to);
        barrier.await();
        if (leader) {
            log.recordEnergy(0, sum(kePartial), sum(pePartial));
            log.markLoopStart();
        }

        for (int step = 1; step <= steps; step++) {
            long t0 = System.nanoTime();

            // A: half-kick + drift + periodic wrap
            updatePositions(from, to);
            barrier.await();
            long tA = System.nanoTime();

            // B: serial cell-list rebuild; positions are final for this step, so the snapshot is taken here
            if (leader) {
                grid.rebuild(particles);
                snapshot(step);
            }
            barrier.await();
            long tB = System.nanoTime();

            // C: forces
            pePartial[t] = computeForces(from, to);
            barrier.await();
            long tC = System.nanoTime();

            // D: half-kick
            kePartial[t] = updateVelocities(from, to);
            barrier.await();
            long tD = System.nanoTime();

            // Other workers cannot overwrite the partial sums before worker 0 reaches the next barrier.
            if (leader) {
                log.recordStep(step, t0, tA, tB, tC, tD);
                if (step % Particles.ENERGY_EVERY == 0 || step == steps) {
                    log.recordEnergy(step, sum(kePartial), sum(pePartial));
                }
            }
        }
    }

    // Writes an XYZ frame when one is due. An I/O error is kept for the end of the run instead of
    // aborting it, matching the Rust version (where stopping worker 0 would hang the barrier).
    private void snapshot(int step) {
        if (snapshots == null || step % snapshotEvery != 0) {
            return;
        }
        try {
            snapshots.writeFrame(step, particles);
        } catch (IOException e) {
            if (snapshotError == null) {
                snapshotError = e;
            }
        }
    }

    private void updatePositions(int from, int to) {
        for (int i = from; i < to; i++) {
            Particle p = particles[i];
            p.vx += 0.5 * Particles.DT * p.fx;
            p.vy += 0.5 * Particles.DT * p.fy;
            p.vz += 0.5 * Particles.DT * p.fz;
            p.x = wrap(p.x + Particles.DT * p.vx);
            p.y = wrap(p.y + Particles.DT * p.vy);
            p.z = wrap(p.z + Particles.DT * p.vz);
        }
    }

    private double wrap(double v) {
        if (v >= boxLength) {
            v -= boxLength;
        } else if (v < 0.0) {
            v += boxLength;
        }
        return v;
    }

    // Every pair is visited twice (no third-law reuse), so workers write only their own forces.
    // Order and form of the arithmetic must match the Rust implementation exactly.
    private double computeForces(int from, int to) {
        int m = grid.m;
        double pe = 0.0;
        for (int i = from; i < to; i++) {
            Particle p = particles[i];
            int cx = grid.coord(p.x);
            int cy = grid.coord(p.y);
            int cz = grid.coord(p.z);
            double fx = 0.0;
            double fy = 0.0;
            double fz = 0.0;
            for (int dz = -1; dz <= 1; dz++) {
                int nz = (cz + dz + m) % m;
                for (int dy = -1; dy <= 1; dy++) {
                    int ny = (cy + dy + m) % m;
                    for (int dx = -1; dx <= 1; dx++) {
                        int nx = (cx + dx + m) % m;
                        for (int j : grid.cells[grid.index(nx, ny, nz)]) {
                            if (j == i) {
                                continue;
                            }
                            Particle q = particles[j];
                            double ddx = p.x - q.x;
                            if (ddx > halfBox) {
                                ddx -= boxLength;
                            } else if (ddx < -halfBox) {
                                ddx += boxLength;
                            }
                            double ddy = p.y - q.y;
                            if (ddy > halfBox) {
                                ddy -= boxLength;
                            } else if (ddy < -halfBox) {
                                ddy += boxLength;
                            }
                            double ddz = p.z - q.z;
                            if (ddz > halfBox) {
                                ddz -= boxLength;
                            } else if (ddz < -halfBox) {
                                ddz += boxLength;
                            }
                            double r2 = ddx * ddx + ddy * ddy + ddz * ddz;
                            if (r2 < Particles.RC2) {
                                double invR2 = 1.0 / r2;
                                double invR6 = invR2 * invR2 * invR2;
                                double fOverR = 24.0 * invR2 * invR6 * (2.0 * invR6 - 1.0);
                                fx += fOverR * ddx;
                                fy += fOverR * ddy;
                                fz += fOverR * ddz;
                                pe += 0.5 * (4.0 * invR6 * (invR6 - 1.0) - Particles.E_SHIFT);
                            }
                        }
                    }
                }
            }
            p.fx = fx;
            p.fy = fy;
            p.fz = fz;
        }
        return pe;
    }

    private double updateVelocities(int from, int to) {
        double ke = 0.0;
        for (int i = from; i < to; i++) {
            Particle p = particles[i];
            p.vx += 0.5 * Particles.DT * p.fx;
            p.vy += 0.5 * Particles.DT * p.fy;
            p.vz += 0.5 * Particles.DT * p.fz;
            ke += 0.5 * (p.vx * p.vx + p.vy * p.vy + p.vz * p.vz);
        }
        return ke;
    }

    private double kineticEnergy(int from, int to) {
        double ke = 0.0;
        for (int i = from; i < to; i++) {
            Particle p = particles[i];
            ke += 0.5 * (p.vx * p.vx + p.vy * p.vy + p.vz * p.vz);
        }
        return ke;
    }

    private static double sum(double[] partials) {
        double s = 0.0;
        for (double v : partials) {
            s += v;
        }
        return s;
    }
}
