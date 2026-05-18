mod generate;
mod ppm;

pub const WIDTH: usize = 4096;
pub const HEIGHT: usize = 4096;
pub const MAX_ITER: u32 = 1000;
pub const RE_MIN: f64 = -2.0_f64;
pub const RE_MAX: f64 = 1.0_f64;
pub const IM_MIN: f64 = -1.5_f64;
pub const IM_MAX: f64 = 1.5_f64;
pub const OUTPUT_PATH: &str = "output/mandelbrot.ppm";

fn main() -> std::io::Result<()> {
    let mut buf = vec![0u8; WIDTH * HEIGHT * 3];
    generate::generate(&mut buf);
    ppm::write_ppm(OUTPUT_PATH, WIDTH, HEIGHT, &buf)?;
    Ok(())
}
