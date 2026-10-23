use std::io::{Error, ErrorKind};
use std::sync::{Barrier, Mutex, RwLock};
use std::thread;
use std::time::Instant;

use crate::data::Snapshots;
use crate::report::{Energy, Recorder};

pub const DT: f64 = 0.005;
pub const RC: f64 = 2.5;
pub const RC2: f64 = RC * RC;
const INV_RC6: f64 = 1.0 / (RC2 * RC2 * RC2);
/// Potential shift 4 (rc^-12 - rc^-6); used only for reported energy, forces are unshifted.
pub const E_SHIFT: f64 = 4.0 * (INV_RC6 * INV_RC6 - INV_RC6);
pub const ENERGY_EVERY: usize = 10;

#[derive(Clone, Copy, Default)]
pub struct Particle {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub vx: f64,
    pub vy: f64,
    pub vz: f64,
    pub fx: f64,
    pub fy: f64,
    pub fz: f64,
}

pub struct Grid {
    pub box_len: f64,
    half_box: f64,
    pub m: usize,
    cell: f64,
}

impl Grid {
    pub fn new(box_len: f64) -> std::io::Result<Self> {
        let m = (box_len / RC).floor() as usize;
        if m < 3 {
            return Err(Error::new(
                ErrorKind::InvalidInput,
                format!("box too small for cell list: M = {} (need >= 3)", m),
            ));
        }
        Ok(Self {
            box_len,
            half_box: 0.5 * box_len,
            m,
            cell: box_len / m as f64,
        })
    }

    fn coord(&self, v: f64) -> usize {
        let c = (v / self.cell) as usize;
        if c >= self.m { self.m - 1 } else { c }
    }
}

/// State shared by all workers. A block and its partial sums are locked by their owner, and by
/// thread 0 only in phase B (blocks) or after the last barrier of a step (partial sums); the
/// barriers keep these apart, so no lock is ever contended.
/// `positions` is the read-only copy of all coordinates that phase C needs, rebuilt in phase B.
struct Shared {
    grid: Grid,
    steps: usize,
    offsets: Vec<usize>,
    blocks: Vec<Mutex<Vec<Particle>>>,
    // Per-thread partial sums, combined by thread 0 in thread order.
    pe_partial: Vec<Mutex<f64>>,
    ke_partial: Vec<Mutex<f64>>,
    positions: RwLock<Vec<[f64; 3]>>,
    cells: RwLock<Vec<Vec<u32>>>,
    barrier: Barrier,
}

fn wrap(v: f64, box_len: f64) -> f64 {
    if v >= box_len {
        v - box_len
    } else if v < 0.0 {
        v + box_len
    } else {
        v
    }
}

/// Phase A: first velocity half-step, drift, periodic wrap.
fn kick_drift(own: &mut [Particle], box_len: f64) {
    for p in own.iter_mut() {
        p.vx += 0.5 * DT * p.fx;
        p.vy += 0.5 * DT * p.fy;
        p.vz += 0.5 * DT * p.fz;
        p.x += DT * p.vx;
        p.y += DT * p.vy;
        p.z += DT * p.vz;
        p.x = wrap(p.x, box_len);
        p.y = wrap(p.y, box_len);
        p.z = wrap(p.z, box_len);
    }
}

/// Phase B (thread 0 only): refreshes the position copy and refills the cell lists.
/// Blocks are visited in ascending order, so every cell lists its indices in ascending order.
fn rebuild_cells(sh: &Shared) {
    let grid = &sh.grid;
    let m = grid.m;
    let mut positions = sh.positions.write().unwrap();
    let mut cells = sh.cells.write().unwrap();
    for c in cells.iter_mut() {
        c.clear();
    }
    for (block, &offset) in sh.blocks.iter().zip(&sh.offsets) {
        let own = block.lock().unwrap();
        for (k, p) in own.iter().enumerate() {
            let i = offset + k;
            positions[i] = [p.x, p.y, p.z];
            let c = (grid.coord(p.z) * m + grid.coord(p.y)) * m + grid.coord(p.x);
            cells[c].push(i as u32);
        }
    }
}

/// Phase C: LJ forces on own particles from the 27 neighbouring cells; returns own share of PE.
/// Every pair is visited twice (no Newton's third law), so nothing outside `own` is written.
fn compute_forces(
    own: &mut [Particle],
    offset: usize,
    positions: &[[f64; 3]],
    cells: &[Vec<u32>],
    grid: &Grid,
) -> f64 {
    let (l, half, m) = (grid.box_len, grid.half_box, grid.m);
    let mut pe = 0.0;
    for (k, p) in own.iter_mut().enumerate() {
        let i = offset + k;
        let [xi, yi, zi] = positions[i];
        let (cx, cy, cz) = (grid.coord(xi), grid.coord(yi), grid.coord(zi));
        let (mut fx, mut fy, mut fz) = (0.0, 0.0, 0.0);
        // d in 0..3 stands for offsets -1, 0, +1: (c + d - 1 + m) % m.
        for dz in 0..3 {
            let nz = (cz + dz + m - 1) % m;
            for dy in 0..3 {
                let ny = (cy + dy + m - 1) % m;
                for dx in 0..3 {
                    let nx = (cx + dx + m - 1) % m;
                    for &j in &cells[(nz * m + ny) * m + nx] {
                        let j = j as usize;
                        if j == i {
                            continue;
                        }
                        let [xj, yj, zj] = positions[j];
                        let mut ddx = xi - xj;
                        if ddx > half { ddx -= l; } else if ddx < -half { ddx += l; }
                        let mut ddy = yi - yj;
                        if ddy > half { ddy -= l; } else if ddy < -half { ddy += l; }
                        let mut ddz = zi - zj;
                        if ddz > half { ddz -= l; } else if ddz < -half { ddz += l; }
                        let r2 = ddx * ddx + ddy * ddy + ddz * ddz;
                        if r2 < RC2 {
                            let inv_r2 = 1.0 / r2;
                            let inv_r6 = inv_r2 * inv_r2 * inv_r2;
                            let f_over_r = 24.0 * inv_r2 * inv_r6 * (2.0 * inv_r6 - 1.0);
                            fx += f_over_r * ddx;
                            fy += f_over_r * ddy;
                            fz += f_over_r * ddz;
                            pe += 0.5 * (4.0 * inv_r6 * (inv_r6 - 1.0) - E_SHIFT);
                        }
                    }
                }
            }
        }
        p.fx = fx;
        p.fy = fy;
        p.fz = fz;
    }
    pe
}

/// Phase C for thread `t`: forces on its own block, partial PE stored for thread 0.
fn forces(sh: &Shared, t: usize) {
    let positions = sh.positions.read().unwrap();
    let cells = sh.cells.read().unwrap();
    let mut own = sh.blocks[t].lock().unwrap();
    let pe = compute_forces(&mut own, sh.offsets[t], &positions, &cells, &sh.grid);
    *sh.pe_partial[t].lock().unwrap() = pe;
}

/// Phase D: second velocity half-step; returns own share of KE.
fn kick(own: &mut [Particle]) -> f64 {
    let mut ke = 0.0;
    for p in own.iter_mut() {
        p.vx += 0.5 * DT * p.fx;
        p.vy += 0.5 * DT * p.fy;
        p.vz += 0.5 * DT * p.fz;
        ke += 0.5 * (p.vx * p.vx + p.vy * p.vy + p.vz * p.vz);
    }
    ke
}

fn kinetic(particles: &[Particle]) -> f64 {
    let mut ke = 0.0;
    for p in particles {
        ke += 0.5 * (p.vx * p.vx + p.vy * p.vy + p.vz * p.vz);
    }
    ke
}

fn sum(partials: &[Mutex<f64>]) -> f64 {
    let mut s = 0.0;
    for v in partials {
        s += *v.lock().unwrap();
    }
    s
}

/// Thread 0 only: step timings, energy log and optional XYZ frames.
struct Leader<'a> {
    recorder: &'a mut Recorder,
    snapshots: Option<&'a mut Snapshots>,
    io_error: Option<std::io::Error>,
}

impl Leader<'_> {
    fn record_energy(&mut self, step: usize, sh: &Shared) {
        let (ke, pe) = (sum(&sh.ke_partial), sum(&sh.pe_partial));
        self.recorder.energy.push(Energy { step, ke, pe });
    }

    /// Writes an XYZ frame when one is due. An I/O error is kept for the end of the run:
    /// stopping thread 0 would leave the other workers waiting on the barrier forever.
    fn snapshot(&mut self, step: usize, positions: &[[f64; 3]]) {
        if let Some(snap) = self.snapshots.as_deref_mut() {
            if step % snap.every == 0 {
                if let Err(e) = snap.write_frame(step, positions) {
                    self.io_error.get_or_insert(e);
                }
            }
        }
    }
}

fn worker(sh: &Shared, t: usize, mut leader: Option<Leader>) -> Option<std::io::Error> {
    // Initialisation (outside the measured loop): cell list, initial forces, step-0 energy.
    if let Some(lead) = leader.as_mut() {
        rebuild_cells(sh);
        lead.snapshot(0, &sh.positions.read().unwrap());
    }
    sh.barrier.wait();
    forces(sh, t);
    let ke = kinetic(&sh.blocks[t].lock().unwrap());
    *sh.ke_partial[t].lock().unwrap() = ke;
    sh.barrier.wait();
    if let Some(lead) = leader.as_mut() {
        lead.record_energy(0, sh);
    }

    let loop_start = Instant::now();
    for step in 1..=sh.steps {
        // Timestamps are taken by every thread for symmetry; only thread 0 records them.
        let t0 = Instant::now();

        // A: half-kick + drift + periodic wrap
        kick_drift(&mut sh.blocks[t].lock().unwrap(), sh.grid.box_len);
        sh.barrier.wait();
        let t1 = Instant::now();

        // B: serial cell-list rebuild; positions are final for this step, so the snapshot is taken here
        if let Some(lead) = leader.as_mut() {
            rebuild_cells(sh);
            lead.snapshot(step, &sh.positions.read().unwrap());
        }
        sh.barrier.wait();
        let t2 = Instant::now();

        // C: forces
        forces(sh, t);
        sh.barrier.wait();
        let t3 = Instant::now();

        // D: half-kick
        let ke = kick(&mut sh.blocks[t].lock().unwrap());
        *sh.ke_partial[t].lock().unwrap() = ke;
        sh.barrier.wait();
        let t4 = Instant::now();

        // Other workers cannot overwrite the partial sums before thread 0 reaches the next barrier.
        if let Some(lead) = leader.as_mut() {
            lead.recorder.record_step(step - 1, loop_start, [t0, t1, t2, t3, t4]);
            if step % ENERGY_EVERY == 0 || step == sh.steps {
                lead.record_energy(step, sh);
            }
        }
    }
    leader.and_then(|lead| lead.io_error)
}

/// Runs the whole simulation on exactly `threads` worker threads: initialisation (cells,
/// initial forces, energy at step 0), then `steps` velocity-Verlet steps.
pub fn simulate(
    particles: Vec<Particle>,
    grid: Grid,
    steps: usize,
    threads: usize,
    snapshots: Option<&mut Snapshots>,
) -> std::io::Result<(Vec<Particle>, Recorder)> {
    let n = particles.len();
    let cell_count = grid.m * grid.m * grid.m;

    // Static partition: thread t owns indices [t*N/P, (t+1)*N/P).
    let offsets: Vec<usize> = (0..=threads).map(|t| t * n / threads).collect();
    let mut rest = particles;
    let mut blocks = Vec::with_capacity(threads);
    for t in (0..threads).rev() {
        blocks.push(Mutex::new(rest.split_off(offsets[t])));
    }
    blocks.reverse();

    let shared = Shared {
        grid,
        steps,
        offsets,
        blocks,
        pe_partial: (0..threads).map(|_| Mutex::new(0.0)).collect(),
        ke_partial: (0..threads).map(|_| Mutex::new(0.0)).collect(),
        positions: RwLock::new(vec![[0.0; 3]; n]),
        cells: RwLock::new(vec![Vec::new(); cell_count]),
        barrier: Barrier::new(threads),
    };

    let mut recorder = Recorder::new(steps);
    let mut leader = Some(Leader {
        recorder: &mut recorder,
        snapshots,
        io_error: None,
    });
    let io_error = thread::scope(|s| {
        let sh = &shared;
        let workers: Vec<_> = (0..threads)
            .map(|t| {
                let lead = leader.take(); // Some only for thread 0
                thread::Builder::new()
                    .name(format!("particles-worker-{}", t))
                    .spawn_scoped(s, move || worker(sh, t, lead))
                    .unwrap()
            })
            .collect();
        // Only thread 0 can report an error; the others are joined when the scope ends.
        workers.into_iter().next().unwrap().join().unwrap()
    });
    if let Some(e) = io_error {
        return Err(e);
    }

    let mut out = Vec::with_capacity(n);
    for block in shared.blocks {
        out.extend(block.into_inner().unwrap());
    }
    Ok((out, recorder))
}
