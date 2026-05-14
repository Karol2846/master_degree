mod mandelbrot;

fn main() -> std::io::Result<()> {
    mandelbrot::run()?;
    // future scenarios will be added here as commented lines:
    // csv::run()?;
    // particles::run()?;
    Ok(())
}
