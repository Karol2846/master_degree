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

    static int polynomialColor(int iter) {
        if (iter == Mandelbrot.MAX_ITER) {
            return 0;
        }
        double t = iter / (double) Mandelbrot.MAX_ITER;
        double omt = 1.0 - t;
        int r = (int) Math.round(9.0  * omt * t * t * t       * 255.0);
        int g = (int) Math.round(15.0 * omt * omt * t * t     * 255.0);
        int b = (int) Math.round(8.5  * omt * omt * omt * t   * 255.0);
        return (r << 16) | (g << 8) | b;
    }

    public static void generate(byte[] buf) {
        for (int py = 0; py < Mandelbrot.HEIGHT; py++) {
            double cy = Mandelbrot.IM_MIN + (py / (Mandelbrot.HEIGHT - 1.0)) * (Mandelbrot.IM_MAX - Mandelbrot.IM_MIN);
            for (int px = 0; px < Mandelbrot.WIDTH; px++) {
                double cx = Mandelbrot.RE_MIN + (px / (Mandelbrot.WIDTH - 1.0)) * (Mandelbrot.RE_MAX - Mandelbrot.RE_MIN);
                int rgb = polynomialColor(escapeIter(cx, cy));
                int offset = (py * Mandelbrot.WIDTH + px) * 3;
                buf[offset]     = (byte) (rgb >>> 16);
                buf[offset + 1] = (byte) (rgb >>> 8);
                buf[offset + 2] = (byte) rgb;
            }
        }
    }
}
