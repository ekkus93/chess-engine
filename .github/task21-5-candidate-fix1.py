from pathlib import Path

path = Path('crates/chess-tools/src/candidate_validation.rs')
text = path.read_text()
old = '''    match game.result() {
        SelfPlayResult::WhiteWin if candidate_color == CandidateColor::White
            | SelfPlayResult::BlackWin if candidate_color == CandidateColor::Black =>
        {
            report.candidate_wins = report
                .candidate_wins
                .checked_add(1)
                .ok_or_else(|| ToolError::new("candidate win count overflow"))?;
        }
        SelfPlayResult::WhiteWin | SelfPlayResult::BlackWin => {
            report.candidate_losses = report
                .candidate_losses
                .checked_add(1)
                .ok_or_else(|| ToolError::new("candidate loss count overflow"))?;
        }
        SelfPlayResult::Draw => {
'''
new = '''    match game.result() {
        SelfPlayResult::WhiteWin | SelfPlayResult::BlackWin => {
            let candidate_won = matches!(
                (game.result(), candidate_color),
                (SelfPlayResult::WhiteWin, CandidateColor::White)
                    | (SelfPlayResult::BlackWin, CandidateColor::Black)
            );
            if candidate_won {
                report.candidate_wins = report
                    .candidate_wins
                    .checked_add(1)
                    .ok_or_else(|| ToolError::new("candidate win count overflow"))?;
            } else {
                report.candidate_losses = report
                    .candidate_losses
                    .checked_add(1)
                    .ok_or_else(|| ToolError::new("candidate loss count overflow"))?;
            }
        }
        SelfPlayResult::Draw => {
'''
if text.count(old) != 1:
    raise SystemExit('unexpected candidate result match')
path.write_text(text.replace(old, new, 1))
