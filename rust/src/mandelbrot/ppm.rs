use std::fs::File;
use std::io::{BufWriter, Write};

pub fn write_ppm(
    path: &str,
    width: usize,
    height: usize,
    pixels: &[u8],
) -> std::io::Result<()> {
    if let Some(parent) = std::path::Path::new(path).parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)?;
        }
    }
    let file = File::create(path)?;
    let mut writer = BufWriter::new(file);
    write!(writer, "P6\n{} {}\n255\n", width, height)?;
    writer.write_all(pixels)?;
    Ok(())
}
