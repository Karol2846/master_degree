use std::fs::File;
use std::io::{BufRead, BufReader, BufWriter, Write};
use std::time::Instant;

const INPUT_PATH: &str = "output/scenario2_transactions.csv";
const OUTPUT_PATH: &str = "output/scenario2_filtered.csv";
const FILTER_TOP_PCT: f64 = 0.01;
const BUFFER_SIZE: usize = 8 * 1024 * 1024;

fn amount_from_line(line: &str) -> f64 {
    line.split(',').nth(2).and_then(|s| s.parse().ok()).unwrap_or(0.0)
}

fn main() -> std::io::Result<()> {
    let file_size_bytes = std::fs::metadata(INPUT_PATH)?.len();
    let wall_start = Instant::now();

    // Pass 1: collect all amounts, sort, compute threshold
    let mut amounts: Vec<f64> = {
        let reader = BufReader::with_capacity(BUFFER_SIZE, File::open(INPUT_PATH)?);
        reader.lines()
            .skip(1)
            .map(|l| amount_from_line(&l.unwrap()))
            .collect()
    };
    amounts.sort_unstable_by(f64::total_cmp);
    let row_count = amounts.len();
    let threshold_idx = (row_count as f64 * (1.0 - FILTER_TOP_PCT)) as usize;
    let threshold = amounts[threshold_idx];
    drop(amounts);

    // Pass 2: filter rows at or above threshold, write to output file
    let reader = BufReader::with_capacity(BUFFER_SIZE, File::open(INPUT_PATH)?);
    let mut writer = BufWriter::with_capacity(BUFFER_SIZE, File::create(OUTPUT_PATH)?);
    let mut lines = reader.lines();

    if let Some(header) = lines.next() {
        writeln!(writer, "{}", header?)?;
    }

    let mut matched = 0usize;
    for line in lines.filter_map(|l| l.ok()) {
        if amount_from_line(&line) >= threshold {
            writeln!(writer, "{}", line)?;
            matched += 1;
        }
    }
    writer.flush()?;

    let elapsed_sec = wall_start.elapsed().as_secs_f64();
    let file_mb = file_size_bytes as f64 / (1024.0 * 1024.0);

    println!(
        "rows_read={} matched={} elapsed_ms={:.2} throughput_rows={:.0}/s throughput_mb={:.1}/s",
        row_count,
        matched,
        elapsed_sec * 1000.0,
        row_count as f64 / elapsed_sec,
        file_mb / elapsed_sec
    );

    Ok(())
}
