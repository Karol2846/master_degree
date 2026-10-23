package org.master.particles;

import java.util.ArrayList;

final class CellGrid {

    final double boxLength;
    final int m;
    final double cellSize;
    final ArrayList<Integer>[] cells;

    @SuppressWarnings({"unchecked", "rawtypes"})
    CellGrid(double boxLength) {
        this.boxLength = boxLength;
        m = (int) Math.floor(boxLength / Particles.RC);
        if (m < 3) {
            throw new IllegalArgumentException("box too small for cell list: M = " + m + " (need >= 3)");
        }
        cellSize = boxLength / m;
        cells = new ArrayList[m * m * m];
        for (int c = 0; c < cells.length; c++) {
            cells[c] = new ArrayList<>();
        }
    }

    int coord(double v) {
        int c = (int) (v / cellSize);
        if (c >= m) {
            c = m - 1;
        }
        return c;
    }

    int index(int cx, int cy, int cz) {
        return (cz * m + cy) * m + cx;
    }

    // Lists are reused across steps; indices are appended in ascending order.
    void rebuild(Particle[] particles) {
        for (ArrayList<Integer> cell : cells) {
            cell.clear();
        }
        for (int i = 0; i < particles.length; i++) {
            Particle p = particles[i];
            cells[index(coord(p.x), coord(p.y), coord(p.z))].add(i);
        }
    }
}
