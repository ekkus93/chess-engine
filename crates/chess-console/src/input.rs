use std::{
    io::{self, BufRead},
    sync::mpsc::{self, Receiver},
    thread::{self, JoinHandle},
};

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum InputEvent {
    Line(String),
    Eof,
    Error(String),
}

/// Owns the receive side plus the process-lifetime reader thread.
///
/// The reader owns only its input handle and event sender. It never owns or
/// mutates game/search state. On piped input/EOF it terminates and can be
/// joined. On an interactive quit while the OS stdin read is blocked, the
/// process may exit with this state-free reader still blocked; engine workers
/// are never treated this way and are always cancelled/joined explicitly.
pub struct InputPump {
    pub receiver: Receiver<InputEvent>,
    handle: Option<JoinHandle<()>>,
}

impl InputPump {
    pub fn stdin() -> io::Result<Self> {
        let (sender, receiver) = mpsc::channel();
        let handle = thread::Builder::new()
            .name("chess-console-stdin".to_owned())
            .spawn(move || {
                let stdin = io::stdin();
                let mut reader = stdin.lock();
                read_events(&mut reader, |event| sender.send(event).is_ok());
            })?;
        Ok(Self {
            receiver,
            handle: Some(handle),
        })
    }

    #[cfg(test)]
    pub(crate) fn from_reader<R>(reader: R) -> io::Result<Self>
    where
        R: BufRead + Send + 'static,
    {
        let (sender, receiver) = mpsc::channel();
        let handle = thread::Builder::new()
            .name("chess-console-test-input".to_owned())
            .spawn(move || {
                let mut reader = reader;
                read_events(&mut reader, |event| sender.send(event).is_ok());
            })?;
        Ok(Self {
            receiver,
            handle: Some(handle),
        })
    }

    pub fn join_if_finished(&mut self) -> io::Result<bool> {
        let Some(handle) = self.handle.as_ref() else {
            return Ok(true);
        };
        if !handle.is_finished() {
            return Ok(false);
        }
        let Some(handle) = self.handle.take() else {
            return Ok(true);
        };
        handle
            .join()
            .map_err(|_| io::Error::other("console input reader panicked"))?;
        Ok(true)
    }
}

fn read_events<R, F>(reader: &mut R, mut send: F)
where
    R: BufRead,
    F: FnMut(InputEvent) -> bool,
{
    loop {
        let mut line = String::new();
        match reader.read_line(&mut line) {
            Ok(0) => {
                let _sent = send(InputEvent::Eof);
                break;
            }
            Ok(_) => {
                while matches!(line.as_bytes().last(), Some(b'\n' | b'\r')) {
                    line.pop();
                }
                if !send(InputEvent::Line(line)) {
                    break;
                }
            }
            Err(error) => {
                let _sent = send(InputEvent::Error(error.to_string()));
                break;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use std::io::Cursor;

    use super::{InputEvent, InputPump};

    #[test]
    fn reader_distinguishes_empty_line_from_eof() {
        let mut pump = InputPump::from_reader(Cursor::new(b"first\n\nlast\r\n".to_vec()))
            .expect("pump starts");
        assert_eq!(
            pump.receiver.recv().expect("event"),
            InputEvent::Line("first".to_owned())
        );
        assert_eq!(
            pump.receiver.recv().expect("event"),
            InputEvent::Line(String::new())
        );
        assert_eq!(
            pump.receiver.recv().expect("event"),
            InputEvent::Line("last".to_owned())
        );
        assert_eq!(pump.receiver.recv().expect("event"), InputEvent::Eof);
        while !pump.join_if_finished().expect("join check") {
            std::thread::yield_now();
        }
    }
}
