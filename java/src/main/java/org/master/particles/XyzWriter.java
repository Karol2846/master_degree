package org.master.particles;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

final class XyzWriter implements AutoCloseable {

    private final BufferedWriter w;

    XyzWriter(Path path) throws IOException {
        if (path.getParent() != null) {
            Files.createDirectories(path.getParent());
        }
        this.w = Files.newBufferedWriter(path, StandardCharsets.US_ASCII);
    }

    void writeFrame(int step, Particle[] particles) throws IOException {
        w.write(particles.length + "\n");
        w.write("step " + step + "\n");
        for (Particle p : particles) {
            w.write(String.format(Locale.ROOT, "Ar %.6f %.6f %.6f\n", p.x, p.y, p.z));
        }
    }

    @Override
    public void close() throws IOException {
        w.close();
    }
}
