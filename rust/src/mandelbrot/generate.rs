use super::{HEIGHT, IM_MAX, IM_MIN, MAX_ITER, RE_MAX, RE_MIN, WIDTH};

fn escape_iter(cx: f64, cy: f64) -> u32 {
    let mut zx = 0.0_f64;
    let mut zy = 0.0_f64;
    let mut iter = 0u32;
    while iter < MAX_ITER && zx * zx + zy * zy <= 4.0 {
        let new_zx = zx * zx - zy * zy + cx;
        zy = 2.0 * zx * zy + cy;
        zx = new_zx;
        iter += 1;
    }
    iter
}

/// Maps escape iteration count to an RGB colour using a polynomial gradient.
/// t = iter / MAX_ITER; each channel is a low-degree polynomial in t.
fn polynomial_color(iter: u32) -> (u8, u8, u8) {
    if iter == MAX_ITER {
        return (0, 0, 0);
    }
    let t = iter as f64 / MAX_ITER as f64;
    let r = (9.0 * (1.0 - t) * t * t * t * 255.0).round() as u8;
    let g = (15.0 * (1.0 - t) * (1.0 - t) * t * t * 255.0).round() as u8;
    let b = (8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t * 255.0).round() as u8;
    (r, g, b)
}

pub fn generate(buf: &mut [u8]) {
    debug_assert_eq!(buf.len(), WIDTH * HEIGHT * 3, "pixel buffer size mismatch");
    for py in 0..HEIGHT {
        let cy = IM_MIN + (py as f64 / (HEIGHT - 1) as f64) * (IM_MAX - IM_MIN);
        for px in 0..WIDTH {
            let cx = RE_MIN + (px as f64 / (WIDTH - 1) as f64) * (RE_MAX - RE_MIN);
            let iter = escape_iter(cx, cy);
            let (r, g, b) = polynomial_color(iter);
            let offset = (py * WIDTH + px) * 3;
            buf[offset] = r;
            buf[offset + 1] = g;
            buf[offset + 2] = b;
        }
    }
}
