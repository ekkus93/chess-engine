use std::{
    io::{self, Write},
    sync::mpsc::Receiver,
};

use chess_app::{GameConfig, DEFAULT_SEARCH_DEPTH, MAX_SEARCH_DEPTH, MIN_SEARCH_DEPTH};
use chess_core::Color;

use crate::input::InputEvent;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MenuSelection {
    Game(GameConfig),
    Quit,
}

pub fn prompt_menu<W: Write>(
    input: &Receiver<InputEvent>,
    output: &mut W,
) -> io::Result<Option<MenuSelection>> {
    loop {
        writeln!(output, "\n1. Human vs Engine")?;
        writeln!(output, "2. Self-play")?;
        writeln!(output, "3. Quit")?;
        write!(output, "Selection [1]: ")?;
        output.flush()?;
        let Some(line) = next_line(input)? else {
            return Ok(None);
        };
        match line.trim().to_ascii_lowercase().as_str() {
            "" | "1" | "human" | "human vs engine" => {
                let Some(config) = prompt_human_config(input, output)? else {
                    return Ok(None);
                };
                return Ok(Some(MenuSelection::Game(config)));
            }
            "2" | "self" | "self-play" | "selfplay" => {
                let Some(config) = prompt_self_play_config(input, output)? else {
                    return Ok(None);
                };
                return Ok(Some(MenuSelection::Game(config)));
            }
            "3" | "q" | "quit" | "exit" => return Ok(Some(MenuSelection::Quit)),
            _ => writeln!(output, "Invalid selection. Choose 1, 2, or 3.")?,
        }
    }
}

fn prompt_human_config<W: Write>(
    input: &Receiver<InputEvent>,
    output: &mut W,
) -> io::Result<Option<GameConfig>> {
    let human_color = loop {
        writeln!(output, "\nPlay as:")?;
        writeln!(output, "1. White")?;
        writeln!(output, "2. Black")?;
        write!(output, "Color [1]: ")?;
        output.flush()?;
        let Some(line) = next_line(input)? else {
            return Ok(None);
        };
        match line.trim().to_ascii_lowercase().as_str() {
            "" | "1" | "white" | "w" => break Color::White,
            "2" | "black" | "b" => break Color::Black,
            _ => writeln!(output, "Invalid color. Choose 1/White or 2/Black.")?,
        }
    };
    let Some(engine_depth) = prompt_depth(input, output, "Engine depth")? else {
        return Ok(None);
    };
    Ok(Some(GameConfig::HumanVsEngine {
        human_color,
        engine_depth,
    }))
}

fn prompt_self_play_config<W: Write>(
    input: &Receiver<InputEvent>,
    output: &mut W,
) -> io::Result<Option<GameConfig>> {
    let Some(white_depth) = prompt_depth(input, output, "White depth")? else {
        return Ok(None);
    };
    let Some(black_depth) = prompt_depth(input, output, "Black depth")? else {
        return Ok(None);
    };
    Ok(Some(GameConfig::SelfPlay {
        white_depth,
        black_depth,
    }))
}

fn prompt_depth<W: Write>(
    input: &Receiver<InputEvent>,
    output: &mut W,
    label: &str,
) -> io::Result<Option<u16>> {
    loop {
        write!(output, "{label} [{DEFAULT_SEARCH_DEPTH}]: ")?;
        output.flush()?;
        let Some(line) = next_line(input)? else {
            return Ok(None);
        };
        let trimmed = line.trim();
        if trimmed.is_empty() {
            return Ok(Some(DEFAULT_SEARCH_DEPTH));
        }
        let Ok(depth) = trimmed.parse::<u16>() else {
            writeln!(
                output,
                "Invalid depth: enter a number from {MIN_SEARCH_DEPTH} to {MAX_SEARCH_DEPTH}."
            )?;
            continue;
        };
        if !(MIN_SEARCH_DEPTH..=MAX_SEARCH_DEPTH).contains(&depth) {
            writeln!(output, "Depth must be from {MIN_SEARCH_DEPTH} to {MAX_SEARCH_DEPTH}; value was not clamped.")?;
            continue;
        }
        return Ok(Some(depth));
    }
}

fn next_line(input: &Receiver<InputEvent>) -> io::Result<Option<String>> {
    match input.recv() {
        Ok(InputEvent::Line(line)) => Ok(Some(line)),
        Ok(InputEvent::Eof) => Ok(None),
        Ok(InputEvent::Error(message)) => Err(io::Error::other(message)),
        Err(_) => Ok(None),
    }
}

#[cfg(test)]
mod tests {
    use std::sync::mpsc;

    use chess_app::GameConfig;
    use chess_core::Color;

    use super::{prompt_menu, MenuSelection};
    use crate::input::InputEvent;

    fn run(lines: &[&str]) -> (Option<MenuSelection>, String) {
        let (sender, receiver) = mpsc::channel();
        for line in lines {
            sender
                .send(InputEvent::Line((*line).to_owned()))
                .expect("send");
        }
        sender.send(InputEvent::Eof).expect("eof");
        drop(sender);
        let mut output = Vec::new();
        let result = prompt_menu(&receiver, &mut output).expect("menu");
        (result, String::from_utf8(output).expect("utf8"))
    }

    #[test]
    fn defaults_choose_human_white_depth_three() {
        let (selection, _) = run(&["", "", ""]);
        assert_eq!(
            selection,
            Some(MenuSelection::Game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: 3,
            }))
        );
    }

    #[test]
    fn human_black_and_self_play_independent_depths_parse() {
        let (black, _) = run(&["1", "2", "5"]);
        assert_eq!(
            black,
            Some(MenuSelection::Game(GameConfig::HumanVsEngine {
                human_color: Color::Black,
                engine_depth: 5,
            }))
        );
        let (self_play, _) = run(&["2", "2", "7"]);
        assert_eq!(
            self_play,
            Some(MenuSelection::Game(GameConfig::SelfPlay {
                white_depth: 2,
                black_depth: 7,
            }))
        );
    }

    #[test]
    fn invalid_depth_is_reprompted_not_clamped() {
        let (selection, output) = run(&["1", "1", "99", "4"]);
        assert_eq!(
            selection,
            Some(MenuSelection::Game(GameConfig::HumanVsEngine {
                human_color: Color::White,
                engine_depth: 4,
            }))
        );
        assert!(output.contains("value was not clamped"));
    }
}
