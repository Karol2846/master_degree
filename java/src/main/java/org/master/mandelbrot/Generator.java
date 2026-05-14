package org.master.mandelbrot;

public class Generator {

    static int escapeIter(double cx, double cy) {
        double zx = 0.0;
        double zy = 0.0;
        int iter = 0;
        while (iter < Mandelbrot.MAX_ITER && zx * zx + zy * zy <= 4.0) {
            double newZx = zx * zx - zy * zy + cx;
            zy = 2.0 * zx * zy + cy;
            zx = newZx;
            iter++;
        }
        return iter;
    }

    public static void generate(byte[] buf) {
        for (int py = 0; py < Mandelbrot.HEIGHT; py++) {
            double cy = Mandelbrot.IM_MIN + (py / (Mandelbrot.HEIGHT - 1.0)) * (Mandelbrot.IM_MAX - Mandelbrot.IM_MIN);
            for (int px = 0; px < Mandelbrot.WIDTH; px++) {
                double cx = Mandelbrot.RE_MIN + (px / (Mandelbrot.WIDTH - 1.0)) * (Mandelbrot.RE_MAX - Mandelbrot.RE_MIN);
                int iter = escapeIter(cx, cy);
                int offset = (py * Mandelbrot.WIDTH + px) * 3;
                if (iter == Mandelbrot.MAX_ITER) {
                    buf[offset]     = 0;
                    buf[offset + 1] = 0;
                    buf[offset + 2] = 0;
                } else {
                    double t = iter / (double) Mandelbrot.MAX_ITER;
                    buf[offset]     = (byte) Math.round(9.0  * (1 - t) * t * t * t         * 255.0);
                    buf[offset + 1] = (byte) Math.round(15.0 * (1 - t) * (1 - t) * t * t   * 255.0);
                    buf[offset + 2] = (byte) Math.round(8.5  * (1 - t) * (1 - t) * (1 - t) * t * 255.0);
                }
            }
        }
    }
}
