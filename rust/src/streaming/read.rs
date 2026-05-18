use std::fs::File;
use std::io::{BufReader, Read};

const RECORD_SIZE: usize = 20;

pub struct Event {
    #[allow(dead_code)]
    pub ts: u64,
    pub sensor_id: u32,
    pub value: f64,
}

pub struct EventReader {
    inner: BufReader<File>,
    buf: [u8; RECORD_SIZE],
}

impl EventReader {
    pub fn open(path: &str) -> std::io::Result<Self> {
        Ok(Self {
            inner: BufReader::with_capacity(64 * 1024, File::open(path)?),
            buf: [0; RECORD_SIZE],
        })
    }

    pub fn read(&mut self) -> std::io::Result<Option<Event>> {
        let mut total = 0usize;
        while total < RECORD_SIZE {
            let n = self.inner.read(&mut self.buf[total..])?;
            if n == 0 {
                if total == 0 {
                    return Ok(None);
                }
                return Err(std::io::Error::new(
                    std::io::ErrorKind::UnexpectedEof,
                    "Truncated event at end of file",
                ));
            }
            total += n;
        }
        let ts = u64::from_le_bytes(self.buf[0..8].try_into().unwrap());
        let sensor_id = u32::from_le_bytes(self.buf[8..12].try_into().unwrap());
        let value = f64::from_le_bytes(self.buf[12..20].try_into().unwrap());
        Ok(Some(Event { ts, sensor_id, value }))
    }
}
