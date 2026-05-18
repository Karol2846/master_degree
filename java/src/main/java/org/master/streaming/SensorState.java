package org.master.streaming;

public class SensorState {
    static final int WINDOW = 128;

    final double[] window = new double[WINDOW];
    int count = 0;
    int writeIdx = 0;
    double sum = 0.0;
    double sumSq = 0.0;

    public void add(double v) {
        if (count == WINDOW) {
            double old = window[writeIdx];
            sum -= old;
            sumSq -= old * old;
        } else {
            count++;
        }
        window[writeIdx] = v;
        sum += v;
        sumSq += v * v;
        writeIdx++;
        if (writeIdx == WINDOW) {
            writeIdx = 0;
        }
    }
}
