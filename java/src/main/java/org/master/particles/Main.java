package org.master.particles;

import java.io.IOException;

public class Main {
    static void main(String[] args) throws InterruptedException {
        Options opts;
        try {
            opts = Options.parse(args);
        } catch (IllegalArgumentException e) {
            System.err.println("error: " + e.getMessage());
            System.err.println(Options.USAGE);
            System.exit(2);
            return;
        }
        try {
            Particles.run(opts);
        } catch (IOException | IllegalArgumentException e) {
            System.err.println("error: " + e.getMessage());
            System.exit(1);
        }
    }
}
