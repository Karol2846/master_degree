package org.master;

import java.io.IOException;

public class Main {
    public static void main(String[] args) throws IOException {
        org.master.mandelbrot.Mandelbrot.run();
        // future scenarios will be added here as commented lines:
        // org.master.csv.CsvFilter.run();
    }
}
