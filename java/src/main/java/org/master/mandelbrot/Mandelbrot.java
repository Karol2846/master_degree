package org.master.mandelbrot;

import java.io.IOException;

public class Mandelbrot {

    static final int WIDTH = 4096;
    static final int HEIGHT = 4096;
    static final int MAX_ITER = 1000;
    static final double RE_MIN = -2.0;
    static final double RE_MAX = 1.0;
    static final double IM_MIN = -1.5;
    static final double IM_MAX = 1.5;
    static final String OUTPUT_PATH = "output/mandelbrot.ppm";

    public static void run() throws IOException {
        byte[] buf = new byte[WIDTH * HEIGHT * 3];
        Generator.generate(buf);
        PpmWriter.write(OUTPUT_PATH, WIDTH, HEIGHT, buf);
    }
}
