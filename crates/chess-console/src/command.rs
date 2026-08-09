use core::fmt;

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Command {
    Move(String),
    Board,
    Moves,
    Status,
    Engine,
    Help,
    Resign,
    Save(String),
    New,
    Menu,
    Quit,
    Pause,
    Resume,
    Step,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum CommandParseError {
    Empty,
    Unknown(String),
    MissingArgument(&'static str),
    UnexpectedArgument(&'static str),
}

impl fmt::Display for CommandParseError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Empty => formatter.write_str("empty input: enter a move or command"),
            Self::Unknown(value) => write!(formatter, "unknown command: {value}"),
            Self::MissingArgument(command) => write!(formatter, "{command} requires an argument"),
            Self::UnexpectedArgument(command) => {
                write!(formatter, "{command} does not accept an argument")
            }
        }
    }
}

impl std::error::Error for CommandParseError {}

pub fn parse_command(input: &str) -> Result<Command, CommandParseError> {
    let trimmed = input.trim();
    if trimmed.is_empty() {
        return Err(CommandParseError::Empty);
    }

    let mut parts = trimmed.split_whitespace();
    let Some(first) = parts.next() else {
        return Err(CommandParseError::Empty);
    };
    let keyword = first.to_ascii_lowercase();

    if keyword == "move" {
        let Some(value) = parts.next() else {
            return Err(CommandParseError::MissingArgument("move"));
        };
        if parts.next().is_some() {
            return Err(CommandParseError::UnexpectedArgument("move"));
        }
        return Ok(Command::Move(value.to_ascii_lowercase()));
    }

    if keyword == "save" {
        let path = trimmed[first.len()..].trim();
        if path.is_empty() {
            return Err(CommandParseError::MissingArgument("save"));
        }
        return Ok(Command::Save(path.to_owned()));
    }

    let simple = match keyword.as_str() {
        "board" => Some(Command::Board),
        "moves" => Some(Command::Moves),
        "status" => Some(Command::Status),
        "engine" => Some(Command::Engine),
        "help" | "?" => Some(Command::Help),
        "resign" => Some(Command::Resign),
        "new" => Some(Command::New),
        "menu" => Some(Command::Menu),
        "quit" | "exit" | "q" => Some(Command::Quit),
        "pause" => Some(Command::Pause),
        "resume" => Some(Command::Resume),
        "step" => Some(Command::Step),
        _ => None,
    };
    if let Some(command) = simple {
        if parts.next().is_some() {
            let name = match keyword.as_str() {
                "?" => "help",
                "exit" | "q" => "quit",
                other => other,
            };
            return Err(CommandParseError::UnexpectedArgument(name));
        }
        return Ok(command);
    }

    if looks_like_uci_token(first) && parts.next().is_none() {
        return Ok(Command::Move(first.to_ascii_lowercase()));
    }

    Err(CommandParseError::Unknown(first.to_owned()))
}

fn looks_like_uci_token(value: &str) -> bool {
    matches!(value.len(), 4 | 5) && value.bytes().all(|byte| byte.is_ascii_alphanumeric())
}

#[cfg(test)]
mod tests {
    use super::{parse_command, Command, CommandParseError};

    #[test]
    fn bare_and_explicit_moves_are_normalized() {
        assert_eq!(
            parse_command(" E2E4 ").expect("move"),
            Command::Move("e2e4".to_owned())
        );
        assert_eq!(
            parse_command("MOVE   E7E8Q").expect("move"),
            Command::Move("e7e8q".to_owned())
        );
    }

    #[test]
    fn command_words_are_case_insensitive_and_whitespace_is_stable() {
        assert_eq!(parse_command("  BoArD  ").expect("board"), Command::Board);
        assert_eq!(parse_command("\tReSuMe\n").expect("resume"), Command::Resume);
        assert_eq!(
            parse_command("save   /tmp/a game.txt ").expect("save"),
            Command::Save("/tmp/a game.txt".to_owned())
        );
    }

    #[test]
    fn empty_unknown_missing_and_extra_arguments_are_visible() {
        assert_eq!(parse_command(" "), Err(CommandParseError::Empty));
        assert_eq!(
            parse_command("foobar"),
            Err(CommandParseError::Unknown("foobar".to_owned()))
        );
        assert_eq!(
            parse_command("save"),
            Err(CommandParseError::MissingArgument("save"))
        );
        assert_eq!(
            parse_command("move"),
            Err(CommandParseError::MissingArgument("move"))
        );
        assert_eq!(
            parse_command("status extra"),
            Err(CommandParseError::UnexpectedArgument("status"))
        );
    }
}
