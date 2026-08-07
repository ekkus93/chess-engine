#![forbid(unsafe_code)]

use std::{error::Error, io};

use crossterm::{
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};

struct TerminalGuard {
    terminal: Terminal<CrosstermBackend<io::Stdout>>,
    restored: bool,
}

impl TerminalGuard {
    fn new() -> io::Result<Self> {
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        if let Err(error) = execute!(stdout, EnterAlternateScreen) {
            let _raw_restore = disable_raw_mode();
            return Err(error);
        }
        let backend = CrosstermBackend::new(stdout);
        match Terminal::new(backend) {
            Ok(terminal) => Ok(Self {
                terminal,
                restored: false,
            }),
            Err(error) => {
                let _raw_restore = disable_raw_mode();
                let mut stdout = io::stdout();
                let _screen_restore = execute!(stdout, LeaveAlternateScreen);
                Err(error)
            }
        }
    }

    fn restore(&mut self) -> io::Result<()> {
        let mut first_error = None;
        if let Err(error) = disable_raw_mode() {
            first_error = Some(error);
        }
        if let Err(error) = execute!(self.terminal.backend_mut(), LeaveAlternateScreen) {
            if first_error.is_none() {
                first_error = Some(error);
            }
        }
        if let Err(error) = self.terminal.show_cursor() {
            if first_error.is_none() {
                first_error = Some(error);
            }
        }
        if let Some(error) = first_error {
            return Err(error);
        }
        self.restored = true;
        Ok(())
    }
}

impl Drop for TerminalGuard {
    fn drop(&mut self) {
        if self.restored {
            return;
        }
        let _raw_restore = disable_raw_mode();
        let _screen_restore = execute!(self.terminal.backend_mut(), LeaveAlternateScreen);
        let _cursor_restore = self.terminal.show_cursor();
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    let mut guard = TerminalGuard::new()?;
    let run_result = chess_tui::ui::run(&mut guard.terminal);
    let restore_result = guard.restore();
    run_result?;
    restore_result?;
    Ok(())
}
