mod data;
mod report;
mod sim;

use std::path::Path;

const SNAPSHOT_PATH: &str = "output/scenario3_snapshots_rust.xyz";
const USAGE: &str = "usage: particles --input <file.bin> --steps <S> --threads <P> \
                     [--snapshot-every <k>] [--dump-final <file.bin>]";

struct Args {
    input: String,
    steps: usize,
    threads: usize,
    snapshot_every: Option<usize>,
    dump_final: Option<String>,
}

fn positive(flag: &str, value: &str) -> Result<usize, String> {
    // Parsed as i32: the same range Java's Integer.parseInt accepts.
    match value.parse::<i32>() {
        Ok(v) if v > 0 => Ok(v as usize),
        _ => Err(format!("{} expects a positive integer, got '{}'", flag, value)),
    }
}

fn parse_args() -> Result<Args, String> {
    let mut input = None;
    let mut steps = None;
    let mut threads = None;
    let mut snapshot_every = None;
    let mut dump_final = None;

    let mut it = std::env::args().skip(1);
    while let Some(flag) = it.next() {
        let value = it.next().ok_or_else(|| format!("missing value for {}", flag))?;
        match flag.as_str() {
            "--input" => input = Some(value),
            "--steps" => steps = Some(positive(&flag, &value)?),
            "--threads" => threads = Some(positive(&flag, &value)?),
            "--snapshot-every" => snapshot_every = Some(positive(&flag, &value)?),
            "--dump-final" => dump_final = Some(value),
            _ => return Err(format!("unknown argument '{}'", flag)),
        }
    }

    Ok(Args {
        input: input.ok_or("missing --input")?,
        steps: steps.ok_or("missing --steps")?,
        threads: threads.ok_or("missing --threads")?,
        snapshot_every,
        dump_final,
    })
}

/// `{:.3e}` with the exponent written like Java's `%.3e` (sign, at least two digits).
fn sci(v: f64) -> String {
    let s = format!("{:.3e}", v);
    match s.split_once('e') {
        Some((mantissa, exp)) => {
            let exp: i32 = exp.parse().unwrap();
            format!("{}e{}{:02}", mantissa, if exp < 0 { '-' } else { '+' }, exp.abs())
        }
        None => s, // NaN
    }
}

fn main() {
    let args = match parse_args() {
        Ok(a) => a,
        Err(msg) => {
            eprintln!("error: {}\n{}", msg, USAGE);
            std::process::exit(2);
        }
    };
    if let Err(e) = run(&args) {
        eprintln!("error: {}", e);
        std::process::exit(1);
    }
}

fn run(args: &Args) -> std::io::Result<()> {
    let (particles, box_len) = data::read_input(&args.input)?;
    let n = particles.len();
    let grid = sim::Grid::new(box_len)?;

    let mut snapshots = match args.snapshot_every {
        Some(every) => Some(data::Snapshots::create(SNAPSHOT_PATH, every)?),
        None => None,
    };
    // The trajectory is flushed even if the simulation failed; the simulation error wins.
    let result = sim::simulate(particles, grid, args.steps, args.threads, snapshots.as_mut());
    let flushed = match snapshots {
        Some(s) => s.finish(),
        None => Ok(()),
    };
    let (particles, recorder) = result?;
    flushed?;

    if let Some(path) = &args.dump_final {
        data::dump_final(path, &particles)?;
    }
    let steps_path = format!("output/scenario3_steps_rust_n{}_p{}.json", n, args.threads);
    recorder.dump_json(Path::new(&steps_path), n, args.threads)?;

    println!(
        "n={} threads={} steps={} loop_ms={:.2} energy_drift={}",
        n,
        args.threads,
        args.steps,
        recorder.loop_ns() as f64 / 1_000_000.0,
        sci(recorder.max_energy_drift())
    );
    Ok(())
}
