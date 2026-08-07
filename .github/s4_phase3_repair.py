from pathlib import Path

path = Path('crates/chess-tools/src/tuning_cli.rs')
text = path.read_text()
old = '''        summary,
        s3.as_ref(),
        s4_trace.as_ref(),
    )?;'''
new = '''        summary,
        s3.as_ref().zip(s4_trace.as_ref()),
    )?;'''
if text.count(old) != 1:
    raise SystemExit('publish call repair anchor missing')
text = text.replace(old, new, 1)
old = '''    summary: chess_tune::SpsaRunSummary,
    s3: Option<&S3GroupContext>,
    s4_trace: Option<&S4OptimizerTrace>,
) -> Result<(), String> {'''
new = '''    summary: chess_tune::SpsaRunSummary,
    group_evidence: Option<(&S3GroupContext, &S4OptimizerTrace)>,
) -> Result<(), String> {'''
if text.count(old) != 1:
    raise SystemExit('publish signature repair anchor missing')
text = text.replace(old, new, 1)
old = '''        if let Some(context) = s3 {
            fs::write(
                staging.join("s3-group.txt"),'''
new = '''        if let Some((context, trace)) = group_evidence {
            fs::write(
                staging.join("s3-group.txt"),'''
if text.count(old) != 1:
    raise SystemExit('group evidence branch anchor missing')
text = text.replace(old, new, 1)
old = '''            let trace = s4_trace.ok_or_else(|| {
                "S3 group tuning requires the S4 optimizer trace artifact".to_owned()
            })?;
            let trace_text = trace.to_text().map_err(|error| error.to_string())?;
            fs::write(staging.join("s4-optimizer-trace.txt"), trace_text)
                .map_err(|error| format!("failed to write S4 optimizer trace: {error}"))?;
        } else if s4_trace.is_some() {
            return Err("S4 optimizer trace is only valid for provenance-bound group tuning".to_owned());
        }'''
new = '''            let trace_text = trace.to_text().map_err(|error| error.to_string())?;
            fs::write(staging.join("s4-optimizer-trace.txt"), trace_text)
                .map_err(|error| format!("failed to write S4 optimizer trace: {error}"))?;
        }'''
if text.count(old) != 1:
    raise SystemExit('trace publication repair anchor missing')
text = text.replace(old, new, 1)
path.write_text(text)
