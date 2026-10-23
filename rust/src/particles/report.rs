use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::Path;
use std::time::Instant;

use crate::sim::DT;

pub struct Energy {
    pub step: usize,
    pub ke: f64,
    pub pe: f64,
}

/// Per-step timings (preallocated, filled by thread 0) and the energy log.
pub struct Recorder {
    pub step_start_ns: Vec<u64>,
    pub step_ns: Vec<u64>,
    pub positions_ns: Vec<u64>,
    pub cells_ns: Vec<u64>,
    pub forces_ns: Vec<u64>,
    pub velocities_ns: Vec<u64>,
    pub energy: Vec<Energy>,
}

fn nanos(from: Instant, to: Instant) -> u64 {
    u64::try_from(to.saturating_duration_since(from).as_nanos()).unwrap_or(u64::MAX)
}

impl Recorder {
    pub fn new(steps: usize) -> Self {
        Self {
            step_start_ns: vec![0; steps],
            step_ns: vec![0; steps],
            positions_ns: vec![0; steps],
            cells_ns: vec![0; steps],
            forces_ns: vec![0; steps],
            velocities_ns: vec![0; steps],
            energy: Vec::with_capacity(steps / 10 + 2),
        }
    }

    /// `marks`: step start, then the moment thread 0 left each of the four barriers.
    pub fn record_step(&mut self, idx: usize, loop_start: Instant, marks: [Instant; 5]) {
        self.step_start_ns[idx] = nanos(loop_start, marks[0]);
        self.positions_ns[idx] = nanos(marks[0], marks[1]);
        self.cells_ns[idx] = nanos(marks[1], marks[2]);
        self.forces_ns[idx] = nanos(marks[2], marks[3]);
        self.velocities_ns[idx] = nanos(marks[3], marks[4]);
        self.step_ns[idx] = nanos(marks[0], marks[4]);
    }

    /// Time from loop start to the end of the last step.
    pub fn loop_ns(&self) -> u64 {
        match self.step_ns.len() {
            0 => 0,
            k => self.step_start_ns[k - 1] + self.step_ns[k - 1],
        }
    }

    /// max |E(t) - E(0)| / |E(0)| over the energy log.
    pub fn max_energy_drift(&self) -> f64 {
        let e0 = self.energy[0].ke + self.energy[0].pe;
        let mut max = 0.0;
        for e in &self.energy[1..] {
            let d = (e.ke + e.pe - e0).abs() / e0.abs();
            // NaN propagates (as in Java's Math.max), so a blown-up run never reports a small drift.
            if d.is_nan() || d > max {
                max = d;
            }
        }
        max
    }

    pub fn dump_json(&self, path: &Path, n: usize, threads: usize) -> std::io::Result<()> {
        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() {
                std::fs::create_dir_all(parent)?;
            }
        }
        let mut w = BufWriter::new(File::create(path)?);
        writeln!(w, "{{")?;
        writeln!(w, "  \"lang\": \"rust\",")?;
        writeln!(w, "  \"n\": {},", n)?;
        writeln!(w, "  \"threads\": {},", threads)?;
        writeln!(w, "  \"steps\": {},", self.step_ns.len())?;
        writeln!(w, "  \"dt\": {},", DT)?;
        write_array(&mut w, "  ", "step_start_ns", &self.step_start_ns, true)?;
        write_array(&mut w, "  ", "step_ns", &self.step_ns, true)?;
        writeln!(w, "  \"phase_ns\": {{")?;
        write_array(&mut w, "    ", "positions", &self.positions_ns, true)?;
        write_array(&mut w, "    ", "cells", &self.cells_ns, true)?;
        write_array(&mut w, "    ", "forces", &self.forces_ns, true)?;
        write_array(&mut w, "    ", "velocities", &self.velocities_ns, false)?;
        writeln!(w, "  }},")?;
        writeln!(w, "  \"energy\": [")?;
        for (k, e) in self.energy.iter().enumerate() {
            let sep = if k + 1 < self.energy.len() { "," } else { "" };
            writeln!(
                w,
                "    {{\"step\": {}, \"ke\": {:?}, \"pe\": {:?}, \"total\": {:?}}}{}",
                e.step,
                e.ke,
                e.pe,
                e.ke + e.pe,
                sep
            )?;
        }
        writeln!(w, "  ]")?;
        writeln!(w, "}}")?;
        w.flush()
    }
}

fn write_array(
    w: &mut impl Write,
    indent: &str,
    key: &str,
    values: &[u64],
    trailing_comma: bool,
) -> std::io::Result<()> {
    write!(w, "{}\"{}\": [", indent, key)?;
    for (k, v) in values.iter().enumerate() {
        if k > 0 {
            write!(w, ", ")?;
        }
        write!(w, "{}", v)?;
    }
    writeln!(w, "]{}", if trailing_comma { "," } else { "" })
}
