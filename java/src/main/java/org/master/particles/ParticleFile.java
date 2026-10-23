package org.master.particles;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;

final class ParticleFile {

    record Input(double boxLength, Particle[] particles) {}

    private static final int HEADER_SIZE = 4 + 8;
    private static final int INPUT_RECORD_SIZE = 6 * 8;
    private static final int FINAL_RECORD_SIZE = 3 * 8;

    // Input: u32 N, f64 L, then N x (x, y, z, vx, vy, vz) as f64, little-endian.
    static Input read(String path) throws IOException {
        byte[] bytes = Files.readAllBytes(Path.of(path));
        if (bytes.length < HEADER_SIZE) {
            throw new IOException("Truncated header");
        }
        ByteBuffer bb = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
        long n = Integer.toUnsignedLong(bb.getInt());
        double boxLength = bb.getDouble();
        long expected = HEADER_SIZE + n * INPUT_RECORD_SIZE;
        if (bytes.length != expected) {
            throw new IOException("Expected " + expected + " bytes for N=" + n + ", got " + bytes.length);
        }
        Particle[] particles = new Particle[(int) n];
        for (int i = 0; i < particles.length; i++) {
            particles[i] = new Particle(
                    bb.getDouble(), bb.getDouble(), bb.getDouble(),
                    bb.getDouble(), bb.getDouble(), bb.getDouble());
        }
        return new Input(boxLength, particles);
    }

    // Final dump: u32 N, then N x (x, y, z) as f64, little-endian.
    static void writeFinal(String path, Particle[] particles) throws IOException {
        Path p = Path.of(path);
        if (p.getParent() != null) {
            Files.createDirectories(p.getParent());
        }
        ByteBuffer bb = ByteBuffer.allocate(4 + particles.length * FINAL_RECORD_SIZE).order(ByteOrder.LITTLE_ENDIAN);
        bb.putInt(particles.length);
        for (Particle q : particles) {
            bb.putDouble(q.x);
            bb.putDouble(q.y);
            bb.putDouble(q.z);
        }
        Files.write(p, bb.array());
    }
}
