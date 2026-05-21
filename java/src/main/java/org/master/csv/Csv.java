package org.master.csv;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;

public class Csv {

    static final String INPUT_PATH = "output/scenario2_transactions.csv";
    static final String OUTPUT_PATH = "output/scenario2_filtered.csv";
    static final double FILTER_TOP_PCT = 0.01;
    static final int BUFFER_SIZE = 8 * 1024 * 1024;

    public static void run() throws IOException {
        long fileSizeBytes = Files.size(Path.of(INPUT_PATH));
        long wallStart = System.nanoTime();

        // Pass 1: collect all amounts, sort, compute threshold
        double[] amounts;
        try (var br = new BufferedReader(new FileReader(INPUT_PATH), BUFFER_SIZE)) {
            amounts = br.lines()
                    .skip(1)
                    .mapToDouble(line -> Double.parseDouble(line.split(",", 4)[2]))
                    .sorted()
                    .toArray();
        }
        int rowCount = amounts.length;
        double threshold = amounts[(int) (rowCount * (1.0 - FILTER_TOP_PCT))];

        // Pass 2: filter rows at or above threshold, stream to output file
        long matched;
        try (var br = new BufferedReader(new FileReader(INPUT_PATH), BUFFER_SIZE);
             var writer = new PrintWriter(new BufferedWriter(new FileWriter(OUTPUT_PATH), BUFFER_SIZE))) {
            String header = br.readLine();
            if (header != null) writer.println(header);
            final double t = threshold;
            matched = br.lines()
                    .filter(line -> Double.parseDouble(line.split(",", 4)[2]) >= t)
                    .peek(writer::println)
                    .count();
        }

        long elapsedNs = System.nanoTime() - wallStart;
        double elapsedSec = elapsedNs / 1e9;
        double fileMb = fileSizeBytes / (1024.0 * 1024.0);

        System.out.printf(
                "rows_read=%d matched=%d elapsed_ms=%.2f throughput_rows=%.0f/s throughput_mb=%.1f/s%n",
                rowCount, matched, elapsedNs / 1_000_000.0, rowCount / elapsedSec, fileMb / elapsedSec);
    }
}
