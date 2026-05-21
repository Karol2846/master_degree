package org.master.mandelbrot;

import java.io.BufferedOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public class PpmWriter {

    public static void write(String path, int width, int height, byte[] pixels) throws IOException {
        Path p = Path.of(path);
        if (p.getParent() != null) {
            Files.createDirectories(p.getParent());
        }
        try (var out = new BufferedOutputStream(Files.newOutputStream(p))) {
            byte[] header = String.format("P6\n%d %d\n255\n", width, height).getBytes(StandardCharsets.US_ASCII);
            out.write(header);
            out.write(pixels);
        }
    }
}
