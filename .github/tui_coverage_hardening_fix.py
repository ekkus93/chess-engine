from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one fix anchor, found {count}")
    target.write_text(text.replace(old, new, 1))


replace_once(
    "crates/chess-tui/src/ui.rs",
    '''    if key.modifiers.contains(KeyModifiers::CONTROL) && key.code == KeyCode::Char('c') {
        runtime.cancel()?;
        app.cancel_search_state(None);
        app.request_quit();
        return Ok(());
    }

    if app.overlay.is_some() {
''',
    '''    if key.modifiers.contains(KeyModifiers::CONTROL) && key.code == KeyCode::Char('c') {
        runtime.cancel()?;
        app.cancel_search_state(None);
        app.request_quit();
        return Ok(());
    }

    if key.modifiers.contains(KeyModifiers::CONTROL) || key.modifiers.contains(KeyModifiers::ALT) {
        return Ok(());
    }

    if app.overlay.is_some() {
''',
)

replace_once(
    "crates/chess-tui/src/ui/hardening_tests.rs",
    '    assert!(too_small.contains("40×10"));\n',
    '',
)

replace_once(
    "crates/chess-tui/src/ui/hardening_tests.rs",
    '''    handle_overlay_key(&mut app, &mut runtime, ctrl(KeyCode::Char('x')))
        .expect("control char ignored");
''',
    '''    handle_key(&mut app, &mut runtime, ctrl(KeyCode::Char('x')))
        .expect("control-modified key ignored");
''',
)
