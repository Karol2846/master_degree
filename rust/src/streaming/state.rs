pub const WINDOW: usize = 128;

pub struct SensorState {
    pub window: [f64; WINDOW],
    pub count: u32,
    pub write_idx: u32,
    pub sum: f64,
    pub sum_sq: f64,
}

impl SensorState {
    pub fn new() -> Self {
        Self {
            window: [0.0; WINDOW],
            count: 0,
            write_idx: 0,
            sum: 0.0,
            sum_sq: 0.0,
        }
    }

    pub fn add(&mut self, v: f64) {
        let idx = self.write_idx as usize;
        if self.count as usize == WINDOW {
            let old = self.window[idx];
            self.sum -= old;
            self.sum_sq -= old * old;
        } else {
            self.count += 1;
        }
        self.window[idx] = v;
        self.sum += v;
        self.sum_sq += v * v;
        self.write_idx += 1;
        if self.write_idx as usize == WINDOW {
            self.write_idx = 0;
        }
    }
}
