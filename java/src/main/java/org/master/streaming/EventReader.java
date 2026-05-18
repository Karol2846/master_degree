package org.master.streaming;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;

public class EventReader implements AutoCloseable {

    public record Event(long ts, int sensorId, double value) {}

    private static final int RECORD_SIZE = 20;
    private final InputStream in;
    private final byte[] buf = new byte[RECORD_SIZE];
    private final ByteBuffer bb = ByteBuffer.wrap(buf).order(ByteOrder.LITTLE_ENDIAN);

    public EventReader(String path) throws IOException {
        this.in = new BufferedInputStream(Files.newInputStream(Path.of(path)), 64 * 1024);
    }

    public Event read() throws IOException {
        int total = 0;
        while (total < RECORD_SIZE) {
            int n = in.read(buf, total, RECORD_SIZE - total);
            if (n == -1) {
                if (total == 0) {
                    return null;
                }
                throw new IOException("Truncated event at end of file");
            }
            total += n;
        }
        bb.position(0);
        long ts = bb.getLong();
        int sid = bb.getInt();
        double value = bb.getDouble();
        return new Event(ts, sid, value);
    }

    @Override
    public void close() throws IOException {
        in.close();
    }
}
