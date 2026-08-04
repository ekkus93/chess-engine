use std::{
    alloc::{GlobalAlloc, Layout, System},
    env,
    hint::black_box,
    process::ExitCode,
    slice,
    sync::atomic::{AtomicBool, AtomicU64, Ordering},
    time::Instant,
};

use chess_core::{
    bishop_attacks, king_attacks, knight_attacks, pawn_attacks, queen_attacks, rook_attacks,
    Bitboard, Color, Position, SearchHistory, Square,
};
use chess_ffi::c_abi::{
    chess_engine_buffer_free, chess_engine_create, chess_engine_destroy,
    chess_engine_get_legal_moves, chess_engine_search, chess_engine_search_result_free,
    ChessEngineBuffer, ChessEngineConfig, ChessEngineHandle, ChessEngineResultCode,
    ChessEngineSearchRequest, ChessEngineSearchResult, CHESS_ENGINE_NULL_HANDLE,
    CHESS_ENGINE_SEARCH_FLAG_NODES,
};
use chess_search::{
    evaluate, iterative_deepening_search_with_limits_and_transposition_table, Score, SearchLimits,
    TranspositionBound, TranspositionEntry, TranspositionProbeRequest, TranspositionScore,
    TranspositionScoreReuse, TranspositionTable,
};
use chess_tools::benchmark_cancellation;

const STARTING_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
const KIWIPETE_FEN: &str = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
const ENDGAME_FEN: &str = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1";
const TACTICAL_FEN: &str =
    "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10";
const POSITION_FENS: [&str; 4] = [STARTING_FEN, KIWIPETE_FEN, ENDGAME_FEN, TACTICAL_FEN];
const SEARCH_NODE_LIMIT: u64 = 20_000;
const FFI_SEARCH_NODE_LIMIT: u64 = 5_000;
const TABLE_MEBIBYTES: usize = 4;

struct CountingAllocator;

static TRACK_ALLOCATIONS: AtomicBool = AtomicBool::new(false);
static ALLOCATION_CALLS: AtomicU64 = AtomicU64::new(0);
static ALLOCATED_BYTES: AtomicU64 = AtomicU64::new(0);
static DEALLOCATION_CALLS: AtomicU64 = AtomicU64::new(0);

unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let pointer = unsafe { System.alloc(layout) };
        if TRACK_ALLOCATIONS.load(Ordering::Relaxed) && !pointer.is_null() {
            ALLOCATION_CALLS.fetch_add(1, Ordering::Relaxed);
            ALLOCATED_BYTES.fetch_add(layout.size() as u64, Ordering::Relaxed);
        }
        pointer
    }

    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        let pointer = unsafe { System.alloc_zeroed(layout) };
        if TRACK_ALLOCATIONS.load(Ordering::Relaxed) && !pointer.is_null() {
            ALLOCATION_CALLS.fetch_add(1, Ordering::Relaxed);
            ALLOCATED_BYTES.fetch_add(layout.size() as u64, Ordering::Relaxed);
        }
        pointer
    }

    unsafe fn dealloc(&self, pointer: *mut u8, layout: Layout) {
        if TRACK_ALLOCATIONS.load(Ordering::Relaxed) && !pointer.is_null() {
            DEALLOCATION_CALLS.fetch_add(1, Ordering::Relaxed);
        }
        unsafe { System.dealloc(pointer, layout) };
    }

    unsafe fn realloc(&self, pointer: *mut u8, layout: Layout, new_size: usize) -> *mut u8 {
        let replacement = unsafe { System.realloc(pointer, layout, new_size) };
        if TRACK_ALLOCATIONS.load(Ordering::Relaxed) && !replacement.is_null() {
            ALLOCATION_CALLS.fetch_add(1, Ordering::Relaxed);
            ALLOCATED_BYTES.fetch_add(new_size as u64, Ordering::Relaxed);
        }
        replacement
    }
}

#[global_allocator]
static GLOBAL_ALLOCATOR: CountingAllocator = CountingAllocator;

#[derive(Clone, Copy, Debug, Default)]
struct AllocationSnapshot {
    calls: u64,
    bytes: u64,
    deallocations: u64,
}

#[derive(Clone, Debug)]
struct BenchmarkSummary {
    name: &'static str,
    samples: usize,
    operations_per_sample: u64,
    median_nanos_per_operation: u128,
    minimum_nanos_per_operation: u128,
    maximum_nanos_per_operation: u128,
    median_allocations_per_sample: u64,
    median_allocated_bytes_per_sample: u64,
    maximum_allocations_per_sample: u64,
    checksum: u64,
}

fn usage() -> &'static str {
    "usage:\n  performance baseline [SAMPLES] [SCALE]\n  performance allocation-audit\n  performance profile-perft\n  performance profile-search"
}

fn parse_positive<T>(value: Option<&String>, default: T, label: &str) -> Result<T, String>
where
    T: std::str::FromStr + Copy + PartialEq + Default,
    T::Err: std::fmt::Display,
{
    let Some(value) = value else {
        return Ok(default);
    };
    let parsed = value
        .parse::<T>()
        .map_err(|error| format!("invalid {label} {value:?}: {error}"))?;
    if parsed == T::default() {
        return Err(format!("{label} must be greater than zero"));
    }
    Ok(parsed)
}

fn start_allocation_tracking() {
    ALLOCATION_CALLS.store(0, Ordering::Relaxed);
    ALLOCATED_BYTES.store(0, Ordering::Relaxed);
    DEALLOCATION_CALLS.store(0, Ordering::Relaxed);
    TRACK_ALLOCATIONS.store(true, Ordering::SeqCst);
}

fn stop_allocation_tracking() -> AllocationSnapshot {
    TRACK_ALLOCATIONS.store(false, Ordering::SeqCst);
    AllocationSnapshot {
        calls: ALLOCATION_CALLS.load(Ordering::Relaxed),
        bytes: ALLOCATED_BYTES.load(Ordering::Relaxed),
        deallocations: DEALLOCATION_CALLS.load(Ordering::Relaxed),
    }
}

fn median_u128(values: &mut [u128]) -> u128 {
    values.sort_unstable();
    values[values.len() / 2]
}

fn median_u64(values: &mut [u64]) -> u64 {
    values.sort_unstable();
    values[values.len() / 2]
}

fn summarize(
    name: &'static str,
    operations_per_sample: u64,
    elapsed: Vec<u128>,
    allocations: Vec<AllocationSnapshot>,
    checksum: u64,
) -> BenchmarkSummary {
    let mut nanos_per_operation: Vec<_> = elapsed
        .into_iter()
        .map(|nanos| nanos / u128::from(operations_per_sample))
        .collect();
    let minimum_nanos_per_operation = *nanos_per_operation
        .iter()
        .min()
        .expect("benchmark has at least one sample");
    let maximum_nanos_per_operation = *nanos_per_operation
        .iter()
        .max()
        .expect("benchmark has at least one sample");
    let median_nanos_per_operation = median_u128(&mut nanos_per_operation);

    let mut allocation_calls: Vec<_> = allocations.iter().map(|value| value.calls).collect();
    let mut allocated_bytes: Vec<_> = allocations.iter().map(|value| value.bytes).collect();
    let maximum_allocations_per_sample = *allocation_calls
        .iter()
        .max()
        .expect("benchmark has allocation samples");
    let median_allocations_per_sample = median_u64(&mut allocation_calls);
    let median_allocated_bytes_per_sample = median_u64(&mut allocated_bytes);

    BenchmarkSummary {
        name,
        samples: nanos_per_operation.len(),
        operations_per_sample,
        median_nanos_per_operation,
        minimum_nanos_per_operation,
        maximum_nanos_per_operation,
        median_allocations_per_sample,
        median_allocated_bytes_per_sample,
        maximum_allocations_per_sample,
        checksum,
    }
}

fn run_benchmark<Operation>(
    name: &'static str,
    samples: usize,
    operations_per_sample: u64,
    mut operation: Operation,
) -> Result<BenchmarkSummary, String>
where
    Operation: FnMut(u64) -> Result<u64, String>,
{
    black_box(operation(0)?);
    let mut elapsed = Vec::with_capacity(samples);
    let mut allocations = Vec::with_capacity(samples);
    let mut checksum = 0_u64;

    for sample in 0..samples {
        start_allocation_tracking();
        let started = Instant::now();
        let mut sample_checksum = 0_u64;
        for iteration in 0..operations_per_sample {
            sample_checksum = sample_checksum.wrapping_add(black_box(operation(iteration)?));
        }
        let elapsed_nanos = started.elapsed().as_nanos();
        let allocation_snapshot = stop_allocation_tracking();
        checksum = checksum
            .rotate_left(7)
            .wrapping_add(sample_checksum)
            .wrapping_add(sample as u64)
            .wrapping_add(allocation_snapshot.deallocations.rotate_left(19));
        elapsed.push(elapsed_nanos);
        allocations.push(allocation_snapshot);
    }

    Ok(summarize(
        name,
        operations_per_sample,
        elapsed,
        allocations,
        checksum,
    ))
}

fn parse_positions() -> Result<Vec<Position>, String> {
    POSITION_FENS
        .iter()
        .map(|fen| Position::from_fen(fen).map_err(|error| error.to_string()))
        .collect()
}

fn square(index: u8) -> Square {
    Square::new(index).expect("benchmark square index is valid")
}

fn leaper_summary(samples: usize, scale: u64) -> Result<BenchmarkSummary, String> {
    run_benchmark(
        "attacks.leaper_lookup",
        samples,
        1_000_000 * scale,
        |iteration| {
            let current = square(black_box((iteration & 63) as u8));
            let color = if iteration & 64 == 0 {
                Color::White
            } else {
                Color::Black
            };
            Ok(pawn_attacks(color, current).bits().rotate_left(3)
                ^ knight_attacks(current).bits().rotate_left(13)
                ^ king_attacks(current).bits().rotate_left(17))
        },
    )
}

fn sliding_summary(samples: usize, scale: u64) -> Result<BenchmarkSummary, String> {
    let occupancies = [
        Bitboard::EMPTY,
        Bitboard::FULL,
        Bitboard::from_bits(0x00ff_0000_00ff_0000),
        Bitboard::from_bits(0x8142_2418_1824_4281),
    ];
    run_benchmark("attacks.sliding_sweep", samples, 2_000 * scale, |_| {
        let mut checksum = 0_u64;
        for occupancy in occupancies {
            for index in 0..Square::COUNT {
                let current = square(index);
                checksum ^= rook_attacks(current, occupancy).bits().rotate_left(5);
                checksum ^= bishop_attacks(current, occupancy).bits().rotate_left(11);
                checksum ^= queen_attacks(current, occupancy).bits().rotate_left(23);
            }
        }
        Ok(checksum)
    })
}

fn legal_moves_summary(samples: usize, scale: u64) -> Result<BenchmarkSummary, String> {
    let mut positions = parse_positions()?;
    let position_count = positions.len() as u64;
    run_benchmark("movegen.legal", samples, 4_000 * scale, |iteration| {
        let index = (iteration % position_count) as usize;
        let moves = positions[index]
            .legal_moves()
            .map_err(|error| error.to_string())?;
        Ok(moves.len() as u64 ^ positions[index].zobrist().rotate_left(9))
    })
}

fn make_unmake_summary(samples: usize, scale: u64) -> Result<BenchmarkSummary, String> {
    let mut position = Position::starting();
    let root = position.clone();
    let token = position
        .legal_move_tokens()
        .map_err(|error| error.to_string())?
        .iter()
        .next()
        .ok_or_else(|| "starting position has no legal token".to_owned())?;
    let summary = run_benchmark("position.make_unmake", samples, 20_000 * scale, |_| {
        let undo = position
            .make_legal_token(token)
            .map_err(|error| error.to_string())?;
        let child_hash = position.zobrist();
        position
            .unmake_move(undo)
            .map_err(|error| error.to_string())?;
        Ok(child_hash ^ position.zobrist().rotate_left(13))
    })?;
    if position != root || position.zobrist() != position.recomputed_zobrist() {
        return Err("make/unmake benchmark did not restore the exact root".to_owned());
    }
    Ok(summary)
}

fn full_hash_summary(samples: usize, scale: u64) -> Result<BenchmarkSummary, String> {
    let positions = parse_positions()?;
    let position_count = positions.len() as u64;
    run_benchmark(
        "hash.full_recompute",
        samples,
        50_000 * scale,
        |iteration| {
            let position = &positions[(iteration % position_count) as usize];
            Ok(position.recomputed_zobrist())
        },
    )
}

fn incremental_hash_summary(samples: usize, scale: u64) -> Result<BenchmarkSummary, String> {
    let mut position = Position::starting();
    let root_hash = position.zobrist();
    let token = position
        .legal_move_tokens()
        .map_err(|error| error.to_string())?
        .iter()
        .next()
        .ok_or_else(|| "starting position has no legal token".to_owned())?;
    let summary = run_benchmark("hash.incremental_update", samples, 20_000 * scale, |_| {
        let undo = position
            .make_legal_token(token)
            .map_err(|error| error.to_string())?;
        let child_hash = position.zobrist();
        if child_hash != position.recomputed_zobrist() {
            return Err("incremental child hash diverged".to_owned());
        }
        position
            .unmake_move(undo)
            .map_err(|error| error.to_string())?;
        if position.zobrist() != root_hash {
            return Err("incremental hash did not restore".to_owned());
        }
        Ok(child_hash ^ root_hash.rotate_left(29))
    })?;
    Ok(summary)
}

fn evaluation_summary(samples: usize, scale: u64) -> Result<BenchmarkSummary, String> {
    let positions = parse_positions()?;
    let position_count = positions.len() as u64;
    run_benchmark("evaluation.full", samples, 10_000 * scale, |iteration| {
        let score = evaluate(&positions[(iteration % position_count) as usize]);
        Ok(score.centipawns() as u32 as u64)
    })
}

fn perft_summary(
    name: &'static str,
    fen: &'static str,
    depth: u8,
    expected: u64,
    samples: usize,
) -> Result<BenchmarkSummary, String> {
    let mut position = Position::from_fen(fen).map_err(|error| error.to_string())?;
    let root = position.clone();
    let summary = run_benchmark(name, samples, 1, |_| {
        let nodes = position.perft(depth).map_err(|error| error.to_string())?;
        if nodes != expected {
            return Err(format!("{name} expected {expected} nodes, found {nodes}"));
        }
        Ok(nodes ^ position.zobrist())
    })?;
    if position != root || position.zobrist() != position.recomputed_zobrist() {
        return Err(format!("{name} did not restore the exact root"));
    }
    Ok(summary)
}

fn fixed_node_search_summary(
    name: &'static str,
    fen: &'static str,
    samples: usize,
) -> Result<BenchmarkSummary, String> {
    let mut elapsed = Vec::with_capacity(samples);
    let mut allocations = Vec::with_capacity(samples);
    let mut checksum = 0_u64;

    for sample in 0..samples {
        let mut position = Position::from_fen(fen).map_err(|error| error.to_string())?;
        let root = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_root = history.clone();
        let mut table =
            TranspositionTable::new(TABLE_MEBIBYTES).map_err(|error| error.to_string())?;
        let limits = SearchLimits::new().with_nodes(SEARCH_NODE_LIMIT);

        start_allocation_tracking();
        let started = Instant::now();
        let result = iterative_deepening_search_with_limits_and_transposition_table(
            &mut position,
            &mut history,
            limits,
            &mut table,
        )
        .map_err(|error| error.to_string())?;
        let elapsed_nanos = started.elapsed().as_nanos();
        let allocation_snapshot = stop_allocation_tracking();

        if position != root
            || history != history_root
            || position.zobrist() != position.recomputed_zobrist()
        {
            return Err(format!("{name} did not restore exact root state"));
        }
        checksum = checksum
            .rotate_left(7)
            .wrapping_add(result.nodes())
            .wrapping_add(result.qnodes().rotate_left(11))
            .wrapping_add(u64::from(result.completed_depth()).rotate_left(17))
            .wrapping_add(sample as u64);
        elapsed.push(elapsed_nanos);
        allocations.push(allocation_snapshot);
    }

    Ok(summarize(name, 1, elapsed, allocations, checksum))
}

fn transposition_store_summary(samples: usize, scale: u64) -> Result<BenchmarkSummary, String> {
    let normalized =
        TranspositionScore::normalize(Score::ZERO, 0).map_err(|error| error.to_string())?;
    let mut table = TranspositionTable::new(TABLE_MEBIBYTES).map_err(|error| error.to_string())?;
    run_benchmark("tt.store", samples, 100_000 * scale, |iteration| {
        let key = iteration
            .wrapping_mul(0x9e37_79b9_7f4a_7c15)
            .rotate_left(17)
            ^ 0xd1b5_4a32_d192_ed03;
        let entry = TranspositionEntry::new(
            key,
            (iteration % 64 + 1) as u16,
            TranspositionBound::Exact,
            normalized,
            None,
            0,
        );
        let result = table.store(entry);
        Ok(key ^ result.cluster_index() as u64 ^ (result.slot_index() as u64).rotate_left(23))
    })
}

fn transposition_probe_summary(samples: usize, scale: u64) -> Result<BenchmarkSummary, String> {
    let normalized =
        TranspositionScore::normalize(Score::ZERO, 0).map_err(|error| error.to_string())?;
    let mut table = TranspositionTable::new(TABLE_MEBIBYTES).map_err(|error| error.to_string())?;
    let fixture_entries = table.entry_capacity().min(16_384);
    for index in 0..fixture_entries {
        let key = index as u64 * 2 + 1;
        table.store(TranspositionEntry::new(
            key,
            32,
            TranspositionBound::Exact,
            normalized,
            None,
            0,
        ));
    }
    run_benchmark("tt.probe", samples, 100_000 * scale, |iteration| {
        let fixture_index = iteration % fixture_entries as u64;
        let key = fixture_index * 2 + if iteration & 3 == 3 { 2 } else { 1 };
        let request = TranspositionProbeRequest::new(
            key,
            16,
            0,
            Score::from_evaluation(-1_000),
            Score::from_evaluation(1_000),
            TranspositionScoreReuse::Allowed,
        );
        let hit = table.probe(request).map_err(|error| error.to_string())?;
        Ok(key ^ u64::from(hit.is_some()))
    })
}

fn cancellation_summary(samples: usize) -> Result<BenchmarkSummary, String> {
    let mut elapsed = Vec::with_capacity(samples);
    let mut allocations = Vec::with_capacity(samples);
    let mut checksum = 0_u64;
    for sample in 0..samples {
        start_allocation_tracking();
        let row = benchmark_cancellation(1).map_err(|error| error.to_string())?;
        let allocation_snapshot = stop_allocation_tracking();
        elapsed.push(row.total_latency_nanos);
        allocations.push(allocation_snapshot);
        checksum = checksum
            .rotate_left(7)
            .wrapping_add(row.checksum)
            .wrapping_add(row.maximum_response_nodes.rotate_left(13))
            .wrapping_add(sample as u64);
    }
    Ok(summarize(
        "cancellation.request_to_observe",
        1,
        elapsed,
        allocations,
        checksum,
    ))
}

fn ensure_code(code: ChessEngineResultCode, operation: &str) -> Result<(), String> {
    if code == ChessEngineResultCode::Ok {
        Ok(())
    } else {
        Err(format!("{operation} returned {code:?}"))
    }
}

fn create_ffi_engine() -> Result<ChessEngineHandle, String> {
    let mut config = ChessEngineConfig::new();
    config.transposition_table_mebibytes = TABLE_MEBIBYTES as u64;
    let mut handle = CHESS_ENGINE_NULL_HANDLE;
    ensure_code(
        unsafe { chess_engine_create(&config, &mut handle) },
        "chess_engine_create",
    )?;
    if handle == CHESS_ENGINE_NULL_HANDLE {
        return Err("chess_engine_create returned a null handle".to_owned());
    }
    Ok(handle)
}

fn ffi_legal_moves_summary(samples: usize, scale: u64) -> Result<BenchmarkSummary, String> {
    let handle = create_ffi_engine()?;
    let result = run_benchmark("ffi.legal_moves", samples, 2_000 * scale, |_| {
        let mut buffer = ChessEngineBuffer::empty();
        ensure_code(
            unsafe { chess_engine_get_legal_moves(handle, &mut buffer) },
            "chess_engine_get_legal_moves",
        )?;
        let bytes = if buffer.len == 0 {
            &[][..]
        } else {
            unsafe { slice::from_raw_parts(buffer.data, buffer.len) }
        };
        let checksum = bytes.iter().fold(buffer.len as u64, |value, byte| {
            value.rotate_left(5) ^ u64::from(*byte)
        });
        ensure_code(
            unsafe { chess_engine_buffer_free(&mut buffer) },
            "chess_engine_buffer_free",
        )?;
        Ok(checksum)
    });
    let destroy = chess_engine_destroy(handle);
    ensure_code(destroy, "chess_engine_destroy")?;
    result
}

fn ffi_search_summary(samples: usize) -> Result<BenchmarkSummary, String> {
    let mut elapsed = Vec::with_capacity(samples);
    let mut allocations = Vec::with_capacity(samples);
    let mut checksum = 0_u64;

    for sample in 0..samples {
        let handle = create_ffi_engine()?;
        let mut request = ChessEngineSearchRequest::new();
        request.flags = CHESS_ENGINE_SEARCH_FLAG_NODES;
        request.nodes = FFI_SEARCH_NODE_LIMIT;
        let mut result = ChessEngineSearchResult::new();

        start_allocation_tracking();
        let started = Instant::now();
        let search_code = unsafe { chess_engine_search(handle, &request, &mut result) };
        let elapsed_nanos = started.elapsed().as_nanos();
        let allocation_snapshot = stop_allocation_tracking();
        ensure_code(search_code, "chess_engine_search")?;

        checksum = checksum
            .rotate_left(7)
            .wrapping_add(result.nodes)
            .wrapping_add(result.qnodes.rotate_left(11))
            .wrapping_add(u64::from(result.completed_depth).rotate_left(19))
            .wrapping_add(sample as u64);
        ensure_code(
            unsafe { chess_engine_search_result_free(&mut result) },
            "chess_engine_search_result_free",
        )?;
        ensure_code(chess_engine_destroy(handle), "chess_engine_destroy")?;
        elapsed.push(elapsed_nanos);
        allocations.push(allocation_snapshot);
    }

    Ok(summarize(
        "ffi.search_nodes",
        1,
        elapsed,
        allocations,
        checksum,
    ))
}

fn print_summaries(summaries: &[BenchmarkSummary]) {
    println!(
        "benchmark\tsamples\toperations_per_sample\tmedian_ns_per_operation\tminimum_ns_per_operation\tmaximum_ns_per_operation\tmedian_allocations_per_sample\tmedian_allocated_bytes_per_sample\tmaximum_allocations_per_sample\tchecksum"
    );
    for row in summaries {
        println!(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
            row.name,
            row.samples,
            row.operations_per_sample,
            row.median_nanos_per_operation,
            row.minimum_nanos_per_operation,
            row.maximum_nanos_per_operation,
            row.median_allocations_per_sample,
            row.median_allocated_bytes_per_sample,
            row.maximum_allocations_per_sample,
            row.checksum
        );
    }
}

fn baseline(samples: usize, scale: u64) -> Result<(), String> {
    let summaries = vec![
        leaper_summary(samples, scale)?,
        sliding_summary(samples, scale)?,
        legal_moves_summary(samples, scale)?,
        make_unmake_summary(samples, scale)?,
        full_hash_summary(samples, scale)?,
        incremental_hash_summary(samples, scale)?,
        evaluation_summary(samples, scale)?,
        perft_summary("perft.starting.depth4", STARTING_FEN, 4, 197_281, samples)?,
        perft_summary("perft.kiwipete.depth3", KIWIPETE_FEN, 3, 97_862, samples)?,
        perft_summary("perft.endgame.depth4", ENDGAME_FEN, 4, 43_238, samples)?,
        fixed_node_search_summary("search.starting.nodes20000", STARTING_FEN, samples)?,
        fixed_node_search_summary("search.tactical.nodes20000", TACTICAL_FEN, samples)?,
        transposition_store_summary(samples, scale)?,
        transposition_probe_summary(samples, scale)?,
        cancellation_summary(samples)?,
        ffi_legal_moves_summary(samples, scale)?,
        ffi_search_summary(samples)?,
    ];
    print_summaries(&summaries);
    Ok(())
}

fn allocation_audit() -> Result<(), String> {
    let summaries = vec![
        leaper_summary(3, 1)?,
        sliding_summary(3, 1)?,
        legal_moves_summary(3, 1)?,
        make_unmake_summary(3, 1)?,
        full_hash_summary(3, 1)?,
        incremental_hash_summary(3, 1)?,
        evaluation_summary(3, 1)?,
        transposition_store_summary(3, 1)?,
        transposition_probe_summary(3, 1)?,
    ];
    for row in &summaries {
        if row.maximum_allocations_per_sample != 0 {
            return Err(format!(
                "{} allocated {} times in a zero-allocation hot path",
                row.name, row.maximum_allocations_per_sample
            ));
        }
    }
    print_summaries(&summaries);
    Ok(())
}

fn profile_perft() -> Result<(), String> {
    let mut position = Position::from_fen(KIWIPETE_FEN).map_err(|error| error.to_string())?;
    let nodes = position.perft(4).map_err(|error| error.to_string())?;
    if nodes != 4_085_603 {
        return Err(format!("profile perft expected 4085603, found {nodes}"));
    }
    println!("profile_perft_nodes\t{nodes}");
    Ok(())
}

fn profile_search() -> Result<(), String> {
    let mut position = Position::from_fen(TACTICAL_FEN).map_err(|error| error.to_string())?;
    let root = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let mut table = TranspositionTable::new(16).map_err(|error| error.to_string())?;
    let result = iterative_deepening_search_with_limits_and_transposition_table(
        &mut position,
        &mut history,
        SearchLimits::new().with_nodes(250_000),
        &mut table,
    )
    .map_err(|error| error.to_string())?;
    if position != root || position.zobrist() != position.recomputed_zobrist() {
        return Err("profile search did not restore exact root".to_owned());
    }
    println!("profile_search_nodes\t{}", result.nodes());
    println!("profile_search_qnodes\t{}", result.qnodes());
    println!("profile_search_depth\t{}", result.completed_depth());
    Ok(())
}

fn run(arguments: &[String]) -> Result<(), String> {
    let command = arguments.first().ok_or_else(|| usage().to_owned())?;
    match command.as_str() {
        "baseline" => {
            if arguments.len() > 3 {
                return Err(usage().to_owned());
            }
            let samples = parse_positive(arguments.get(1), 7_usize, "sample count")?;
            let scale = parse_positive(arguments.get(2), 1_u64, "scale")?;
            baseline(samples, scale)
        }
        "allocation-audit" if arguments.len() == 1 => allocation_audit(),
        "profile-perft" if arguments.len() == 1 => profile_perft(),
        "profile-search" if arguments.len() == 1 => profile_search(),
        _ => Err(usage().to_owned()),
    }
}

fn main() -> ExitCode {
    let arguments: Vec<_> = env::args().skip(1).collect();
    match run(&arguments) {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("error: {error}");
            ExitCode::FAILURE
        }
    }
}
