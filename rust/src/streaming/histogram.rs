use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::Path;

pub const BUCKETS: usize = 64;
const MAX_SHIFT: usize = 56;

pub struct Histogram {
    pub buckets: [u64; BUCKETS],
    pub total: u64,
    pub min_ns: u64,
    pub max_ns: u64,
    pub sum_ns: u128,
}

impl Histogram {
    pub fn new() -> Self {
        Self {
            buckets: [0; BUCKETS],
            total: 0,
            min_ns: u64::MAX,
            max_ns: 0,
            sum_ns: 0,
        }
    }

    pub fn record(&mut self, nanos: u64) {
        let scaled = (nanos / 100).max(1);
        let b = 63 - scaled.leading_zeros() as i32;
        let b = b.clamp(0, BUCKETS as i32 - 1) as usize;
        self.buckets[b] += 1;
        self.total += 1;
        if nanos < self.min_ns {
            self.min_ns = nanos;
        }
        if nanos > self.max_ns {
            self.max_ns = nanos;
        }
        self.sum_ns += nanos as u128;
    }

    pub fn percentile(&self, pct: f64) -> u64 {
        if self.total == 0 {
            return 0;
        }
        let target = ((self.total as f64) * pct / 100.0).ceil() as u64;
        let mut running: u64 = 0;
        for i in 0..BUCKETS {
            running += self.buckets[i];
            if running >= target {
                return Self::bucket_upper_bound(i);
            }
        }
        self.max_ns
    }

    pub fn bucket_lower_bound(i: usize) -> u64 {
        if i >= MAX_SHIFT {
            u64::MAX
        } else {
            100u64 << i
        }
    }

    pub fn bucket_upper_bound(i: usize) -> u64 {
        if i >= BUCKETS - 1 {
            u64::MAX
        } else {
            Self::bucket_lower_bound(i + 1)
        }
    }

    pub fn min_ns(&self) -> u64 {
        if self.min_ns == u64::MAX { 0 } else { self.min_ns }
    }

    pub fn mean_ns(&self) -> f64 {
        if self.total == 0 {
            0.0
        } else {
            self.sum_ns as f64 / self.total as f64
        }
    }

    pub fn dump_json(&self, path: &Path) -> std::io::Result<()> {
        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() {
                std::fs::create_dir_all(parent)?;
            }
        }
        let mut w = BufWriter::new(File::create(path)?);
        writeln!(w, "{{")?;
        writeln!(w, "  \"total_events\": {},", self.total)?;
        writeln!(w, "  \"min_ns\": {},", self.min_ns())?;
        writeln!(w, "  \"max_ns\": {},", self.max_ns)?;
        writeln!(w, "  \"mean_ns\": {},", self.mean_ns())?;
        writeln!(w, "  \"p50_ns\": {},", self.percentile(50.0))?;
        writeln!(w, "  \"p95_ns\": {},", self.percentile(95.0))?;
        writeln!(w, "  \"p99_ns\": {},", self.percentile(99.0))?;
        writeln!(w, "  \"p999_ns\": {},", self.percentile(99.9))?;
        write!(w, "  \"buckets\": [")?;
        for i in 0..BUCKETS {
            if i > 0 {
                write!(w, ", ")?;
            }
            write!(w, "{}", self.buckets[i])?;
        }
        writeln!(w, "],")?;
        write!(w, "  \"bucket_lower_ns\": [")?;
        for i in 0..BUCKETS {
            if i > 0 {
                write!(w, ", ")?;
            }
            write!(w, "{}", Self::bucket_lower_bound(i))?;
        }
        writeln!(w, "]")?;
        writeln!(w, "}}")?;
        Ok(())
    }
}
