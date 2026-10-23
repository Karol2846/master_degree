use std::fs::File;
use std::io::{BufWriter, Error, ErrorKind, Write};
use std::path::Path;

use crate::sim::Particle;

const HEADER_SIZE: usize = 12;
const RECORD_SIZE: usize = 48;

fn create_parent(path: &Path) -> std::io::Result<()> {
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)?;
        }
    }
    Ok(())
}

fn f64_at(bytes: &[u8], offset: usize) -> f64 {
    f64::from_le_bytes(bytes[offset..offset + 8].try_into().unwrap())
}

/// Reads `u32 N, f64 L, N x (x, y, z, vx, vy, vz)` (little-endian); forces start at zero.
pub fn read_input(path: &str) -> std::io::Result<(Vec<Particle>, f64)> {
    let bytes = std::fs::read(path)?;
    if bytes.len() < HEADER_SIZE {
        return Err(Error::new(ErrorKind::UnexpectedEof, "Truncated header"));
    }
    let n = u32::from_le_bytes(bytes[0..4].try_into().unwrap()) as usize;
    let box_len = f64_at(&bytes, 4);
    if bytes.len() != HEADER_SIZE + n * RECORD_SIZE {
        return Err(Error::new(
            ErrorKind::InvalidData,
            format!("Expected {} bytes for N={}, got {}", HEADER_SIZE + n * RECORD_SIZE, n, bytes.len()),
        ));
    }
    let mut particles = Vec::with_capacity(n);
    for i in 0..n {
        let o = HEADER_SIZE + i * RECORD_SIZE;
        particles.push(Particle {
            x: f64_at(&bytes, o),
            y: f64_at(&bytes, o + 8),
            z: f64_at(&bytes, o + 16),
            vx: f64_at(&bytes, o + 24),
            vy: f64_at(&bytes, o + 32),
            vz: f64_at(&bytes, o + 40),
            ..Particle::default()
        });
    }
    Ok((particles, box_len))
}

/// Writes final positions: `u32 N`, then `N x (x, y, z)` as little-endian f64.
pub fn dump_final(path: &str, particles: &[Particle]) -> std::io::Result<()> {
    create_parent(Path::new(path))?;
    let mut w = BufWriter::new(File::create(path)?);
    w.write_all(&(particles.len() as u32).to_le_bytes())?;
    for p in particles {
        w.write_all(&p.x.to_le_bytes())?;
        w.write_all(&p.y.to_le_bytes())?;
        w.write_all(&p.z.to_le_bytes())?;
    }
    w.flush()
}

/// XYZ trajectory writer (visualisation only, never used in measured runs).
pub struct Snapshots {
    pub every: usize,
    writer: BufWriter<File>,
}

impl Snapshots {
    pub fn create(path: &str, every: usize) -> std::io::Result<Self> {
        create_parent(Path::new(path))?;
        Ok(Self {
            every,
            writer: BufWriter::new(File::create(path)?),
        })
    }

    pub fn write_frame(&mut self, step: usize, positions: &[[f64; 3]]) -> std::io::Result<()> {
        writeln!(self.writer, "{}", positions.len())?;
        writeln!(self.writer, "step {}", step)?;
        for [x, y, z] in positions {
            writeln!(self.writer, "Ar {:.6} {:.6} {:.6}", x, y, z)?;
        }
        Ok(())
    }

    pub fn finish(mut self) -> std::io::Result<()> {
        self.writer.flush()
    }
}
