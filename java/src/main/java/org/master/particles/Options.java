package org.master.particles;

record Options(String input, int steps, int threads, int snapshotEvery, String dumpFinal) {

    static final String USAGE =
            "usage: particles --input <file.bin> --steps <S> --threads <P> [--snapshot-every <k>] [--dump-final <file.bin>]";

    static Options parse(String[] args) {
        String input = null;
        int steps = -1;
        int threads = -1;
        int snapshotEvery = 0;
        String dumpFinal = null;
        for (int i = 0; i < args.length; i++) {
            String flag = args[i];
            if (i + 1 >= args.length) {
                throw new IllegalArgumentException("missing value for " + flag);
            }
            String value = args[++i];
            switch (flag) {
                case "--input" -> input = value;
                case "--steps" -> steps = parsePositive(flag, value);
                case "--threads" -> threads = parsePositive(flag, value);
                case "--snapshot-every" -> snapshotEvery = parsePositive(flag, value);
                case "--dump-final" -> dumpFinal = value;
                default -> throw new IllegalArgumentException("unknown argument '" + flag + "'");
            }
        }
        if (input == null) {
            throw new IllegalArgumentException("missing --input");
        }
        if (steps < 0) {
            throw new IllegalArgumentException("missing --steps");
        }
        if (threads < 0) {
            throw new IllegalArgumentException("missing --threads");
        }
        return new Options(input, steps, threads, snapshotEvery, dumpFinal);
    }

    private static int parsePositive(String flag, String value) {
        int v;
        try {
            v = Integer.parseInt(value);
        } catch (NumberFormatException e) {
            v = 0;
        }
        if (v < 1) {
            throw new IllegalArgumentException(flag + " expects a positive integer, got '" + value + "'");
        }
        return v;
    }
}
