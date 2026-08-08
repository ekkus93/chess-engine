from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one patch anchor, found {count}")
    target.write_text(text.replace(old, new, 1))


def append_once(path: str, marker: str, addition: str) -> None:
    target = Path(path)
    text = target.read_text()
    if marker in text:
        return
    if not text.endswith("\n"):
        text += "\n"
    target.write_text(text + addition)


worker_impl_old = '''    pub fn cancel_and_join(&mut self) -> Result<(), SearchWorkerError> {
        self.discard_final.store(true, Ordering::Release);
        self.stop_flag.request_stop();
        self.join()
    }
}
'''
worker_impl_new = '''    pub fn cancel_and_join(&mut self) -> Result<(), SearchWorkerError> {
        self.discard_final.store(true, Ordering::Release);
        self.stop_flag.request_stop();
        self.join()
    }

    #[cfg(test)]
    pub(crate) fn finished_with_events_for_test(
        events: Vec<EngineEvent>,
    ) -> (Self, Receiver<EngineEvent>) {
        let stop_flag = SearchStopFlag::new();
        let discard_final = Arc::new(AtomicBool::new(false));
        let (sender, receiver) = mpsc::channel();
        for event in events {
            sender.send(event).expect("synthetic event receiver remains open");
        }
        drop(sender);
        let handle = thread::spawn(|| Ok(()));
        while !handle.is_finished() {
            thread::yield_now();
        }
        (
            Self {
                stop_flag,
                discard_final,
                handle: Some(handle),
            },
            receiver,
        )
    }

    #[cfg(test)]
    pub(crate) fn waiting_with_event_for_test(
        event: EngineEvent,
    ) -> (Self, Receiver<EngineEvent>) {
        let stop_flag = SearchStopFlag::new();
        let discard_final = Arc::new(AtomicBool::new(false));
        let worker_discard = Arc::clone(&discard_final);
        let (sender, receiver) = mpsc::channel();
        sender
            .send(event)
            .expect("synthetic event receiver remains open");
        drop(sender);
        let handle = thread::spawn(move || {
            while !worker_discard.load(Ordering::Acquire) {
                thread::yield_now();
            }
            Ok(())
        });
        (
            Self {
                stop_flag,
                discard_final,
                handle: Some(handle),
            },
            receiver,
        )
    }

    #[cfg(test)]
    pub(crate) fn finished_without_event_for_test() -> (Self, Receiver<EngineEvent>) {
        let stop_flag = SearchStopFlag::new();
        let discard_final = Arc::new(AtomicBool::new(false));
        let (sender, receiver) = mpsc::channel();
        drop(sender);
        let handle = thread::spawn(|| Ok(()));
        while !handle.is_finished() {
            thread::yield_now();
        }
        (
            Self {
                stop_flag,
                discard_final,
                handle: Some(handle),
            },
            receiver,
        )
    }

    #[cfg(test)]
    pub(crate) fn panicking_for_test() -> (Self, Receiver<EngineEvent>) {
        let stop_flag = SearchStopFlag::new();
        let discard_final = Arc::new(AtomicBool::new(false));
        let (sender, receiver) = mpsc::channel();
        drop(sender);
        let handle = thread::spawn(|| -> Result<(), SearchWorkerError> {
            panic!("synthetic TUI search worker panic")
        });
        while !handle.is_finished() {
            thread::yield_now();
        }
        (
            Self {
                stop_flag,
                discard_final,
                handle: Some(handle),
            },
            receiver,
        )
    }
}
'''
replace_once("crates/chess-tui/src/worker.rs", worker_impl_old, worker_impl_new)

finish_old = '''    if let Some(best_move) = result.completed().best_move() {
        let Some(metrics) = SearchMetrics::from_result(&result) else {
            send_event(
                sender,
                EngineEvent::Failed {
                    ticket,
                    message: "search returned an exact move without an exact iteration".to_owned(),
                },
            )?;
            return Ok(());
        };
        send_event(
            sender,
            EngineEvent::Completed {
                ticket,
                best_move,
                metrics,
            },
        )?;
        return Ok(());
    }

    let message = if result.fallback().is_some() {
        "search ended before completing depth one; TUI rejected the search fallback".to_owned()
    } else {
        "search completed without an exact best move".to_owned()
    };
    send_event(sender, EngineEvent::Failed { ticket, message })?;
    Ok(())
}
'''
finish_new = '''    let event = classify_success(
        ticket,
        result.completed().best_move(),
        SearchMetrics::from_result(&result),
        result.fallback().is_some(),
    );
    send_event(sender, event)
}

fn classify_success(
    ticket: SearchTicket,
    best_move: Option<Move>,
    metrics: Option<SearchMetrics>,
    has_fallback: bool,
) -> EngineEvent {
    match (best_move, metrics, has_fallback) {
        (Some(best_move), Some(metrics), _) => EngineEvent::Completed {
            ticket,
            best_move,
            metrics,
        },
        (Some(_), None, _) => EngineEvent::Failed {
            ticket,
            message: "search returned an exact move without an exact iteration".to_owned(),
        },
        (None, _, true) => EngineEvent::Failed {
            ticket,
            message: "search ended before completing depth one; TUI rejected the search fallback"
                .to_owned(),
        },
        (None, _, false) => EngineEvent::Failed {
            ticket,
            message: "search completed without an exact best move".to_owned(),
        },
    }
}
'''
replace_once("crates/chess-tui/src/worker.rs", finish_old, finish_new)
append_once(
    "crates/chess-tui/src/worker.rs",
    "mod hardening_tests;",
    "\n#[cfg(test)]\nmod hardening_tests;\n",
)

ui_spawn_old = '''        if self.active.is_none() {
            if let Some(request) = app.take_pending_search() {
                let ticket = request.ticket;
                match SearchWorker::spawn(request) {
                    Ok((worker, receiver)) => {
                        self.active = Some(ActiveWorker {
                            ticket,
                            worker,
                            receiver,
                        });
                    }
                    Err(error) => {
                        if let Err(app_error) = app.handle_engine_event(EngineEvent::Failed {
                            ticket,
                            message: error.to_string(),
                        }) {
                            app.cancel_search_state(Some(format!(
                                "Search spawn failed: {app_error}"
                            )));
                        }
                    }
                }
            }
        }
        Ok(())
    }

    fn cancel(&mut self) -> io::Result<()> {
'''
ui_spawn_new = '''        if self.active.is_none() {
            if let Some(request) = app.take_pending_search() {
                let ticket = request.ticket;
                let spawn_result = SearchWorker::spawn(request);
                self.handle_spawn_result(app, ticket, spawn_result)?;
            }
        }
        Ok(())
    }

    fn handle_spawn_result(
        &mut self,
        app: &mut AppState,
        ticket: SearchTicket,
        spawn_result: Result<(SearchWorker, Receiver<EngineEvent>), SearchWorkerError>,
    ) -> Result<(), SearchWorkerError> {
        match spawn_result {
            Ok((worker, receiver)) => {
                self.active = Some(ActiveWorker {
                    ticket,
                    worker,
                    receiver,
                });
            }
            Err(error) => {
                if let Err(app_error) = app.handle_engine_event(EngineEvent::Failed {
                    ticket,
                    message: error.to_string(),
                }) {
                    app.cancel_search_state(Some(format!("Search spawn failed: {app_error}")));
                }
            }
        }
        Ok(())
    }

    fn cancel(&mut self) -> io::Result<()> {
'''
replace_once("crates/chess-tui/src/ui.rs", ui_spawn_old, ui_spawn_new)

save_no_session_old = '''    let Some(session) = app.session.as_ref() else {
        app.mark_save_failed("Save failed: no game exists".to_owned());
        return Ok(());
    };
'''
save_no_session_new = '''    let Some(session) = app.session.as_ref() else {
        app.dismiss_overlay();
        return Err(io::Error::other("Save failed: no game exists"));
    };
'''
replace_once("crates/chess-tui/src/ui.rs", save_no_session_old, save_no_session_new)
append_once(
    "crates/chess-tui/src/ui.rs",
    "mod hardening_tests;",
    "\n#[cfg(test)]\nmod hardening_tests;\n",
)

for module in ["app", "render", "save"]:
    append_once(
        f"crates/chess-tui/src/{module}.rs",
        "mod hardening_tests;",
        "\n#[cfg(test)]\nmod hardening_tests;\n",
    )

replace_once(
    "crates/chess-tui/src/ui/hardening_tests.rs",
    "kind: io::ErrorKind::ResourceBusy,",
    "kind: io::ErrorKind::Other,",
)

dev_usage_old = '''  tui                               Run the native Rust terminal interface.\n  android'''
dev_usage_new = '''  tui                               Run the native Rust terminal interface.\n  tui-coverage COMMAND              Run focused Rust TUI llvm-cov coverage.\n  android'''
replace_once("scripts/dev.sh", dev_usage_old, dev_usage_new)

dev_case_old = '''  tui)\n    [[ $# -eq 0 ]] || { usage; exit 2; }\n    cargo run --locked -p chess-tui\n    ;;\n  android)'''
dev_case_new = '''  tui)\n    [[ $# -eq 0 ]] || { usage; exit 2; }\n    cargo run --locked -p chess-tui\n    ;;\n  tui-coverage)\n    [[ $# -eq 1 ]] || { usage; exit 2; }\n    bash scripts/tui_coverage.sh "$1"\n    ;;\n  android)'''
replace_once("scripts/dev.sh", dev_case_old, dev_case_new)

workflow_doc = Path("docs/RUST_DEVELOPER_WORKFLOWS.md")
workflow_text = workflow_doc.read_text()
coverage_section = '''## Rust TUI coverage\n\nFocused source-based coverage for the native Rust TUI uses `cargo-llvm-cov` as diagnostic evidence. Coverage is intentionally separate from the Rust 1.75 product MSRV gate: CI runs coverage on the current stable Rust toolchain with `llvm-tools-preview`, while product compatibility remains validated independently. The permanent workflow pins `cargo-llvm-cov` 0.8.7.\n\nInstall a compatible `cargo-llvm-cov` locally and ensure `llvm-tools-preview` is present, then use:\n\n```bash\nbash scripts/dev.sh tui-coverage clean\nbash scripts/dev.sh tui-coverage summary\nbash scripts/dev.sh tui-coverage json\nbash scripts/dev.sh tui-coverage lcov\nbash scripts/dev.sh tui-coverage html\n```\n\nThe JSON summary is written to `target/chess-tui-coverage-summary.json`, LCOV to `target/chess-tui-lcov.info`, and HTML under `target/llvm-cov/html/`. `target/` is ignored. Coverage commands run the relevant `chess-tui` tests with all features and do not enforce an arbitrary percentage threshold; uncovered safety/error branches are reviewed explicitly. The permanent `Rust TUI coverage` workflow uploads text, JSON, and LCOV evidence tied to the tested commit SHA without requiring Codecov or another external coverage service. Coverage tooling is development infrastructure and is not a `chess-tui` runtime dependency.\n\n'''
if "## Rust TUI coverage" not in workflow_text:
    anchor = "## Android/JNI\n"
    if workflow_text.count(anchor) != 1:
        raise SystemExit("developer workflow coverage insertion anchor mismatch")
    workflow_doc.write_text(workflow_text.replace(anchor, coverage_section + anchor, 1))

ci = Path(".github/workflows/ci.yml")
ci_text = ci.read_text()
ci_text = ci_text.replace(
    "          test -f scripts/dev.sh\n",
    "          test -f scripts/dev.sh\n          test -f scripts/tui_coverage.sh\n          test -f .github/workflows/tui-coverage.yml\n",
    1,
)
ci_text = ci_text.replace(
    "            scripts/dev.sh \\\n",
    "            scripts/dev.sh \\\n            scripts/tui_coverage.sh \\\n",
    1,
)
ci.write_text(ci_text)
