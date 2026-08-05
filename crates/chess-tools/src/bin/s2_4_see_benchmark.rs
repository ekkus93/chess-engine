use std::{
    alloc::{GlobalAlloc, Layout, System},
    env,
    hint::black_box,
    process::ExitCode,
    sync::atomic::{AtomicBool, AtomicU64, Ordering},
    time::Instant,
};

use chess_core::{
    static_exchange_evaluation, static_exchange_semantic_checksum, Move, Position, UciMove,
};

const DEFAULT_SAMPLES: usize = 7;
const OPERATIONS_PER_SAMPLE: u64 = 50_000;
const FIXTURES: [(&str, &str); 4] = [
    ("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5"),
    ("4k3/4n3/8/3p4/2P5/8/8/4R1K1 w - - 0 1", "c4d5"),
    ("3r2k1/8/8/3pP3/8/8/8/6K1 w - d6 0 1", "e5d6"),
    ("1r5k/P7/8/8/8/8/8/7K w - - 0 1", "a7b8q"),
];

struct CountingAllocator;

static TRACK_ALLOCATIONS: AtomicBool = AtomicBool::new(false);
static ALLOCATION_CALLS: AtomicU64 = AtomicU64::new(0);

unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let pointer = unsafe { System.alloc(layout) };
        if TRACK_ALLOCATIONS.load(Ordering::Relaxed) && !pointer.is_null() {
            ALLOCATION_CALLS.fetch_add(1, Ordering::Relaxed);
        }
        pointer
    }

    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        let pointer = unsafe { System.alloc_zeroed(layout) };
        if TRACK_ALLOCATIONS.load(Ordering::Relaxed) && !pointer.is_null() {
            ALLOCATION_CALLS.fetch_add(1, Ordering::Relaxed);
        }
        pointer
    }

    unsafe fn dealloc(&self, pointer: *mut u8, layout: Layout) {
        unsafe { System.dealloc(pointer, layout) };
    }

    unsafe fn realloc(&self, pointer: *mut u8, layout: Layout, new_size: usize) -> *mut u8 {
        let replacement = unsafe { System.realloc(pointer, layout, new_size) };
        if TRACK_ALLOCATIONS.load(Ordering::Relaxed) && !replacement.is_null() {
            ALLOCATION_CALLS.fetch_add(1, Ordering::Relaxed);
        }
        replacement
    }
}

#[global_allocator]
static GLOBAL_ALLOCATOR: CountingAllocator = CountingAllocator;

struct Fixture {
    position: Position,
    current: Move,
}

fn parse_samples() -> Result<usize, String> {
    let Some(value) = env::args().nth(1) else {
        return Ok(DEFAULT_SAMPLES);
    };
    let parsed = value
        .parse::<usize>()
        .map_err(|error| format!("invalid sample count {value:?}: {error}"))?;
    if parsed == 0 {
        return Err("sample count must be greater than zero".to_owned());
    }
    Ok(parsed)
}

fn fixtures() -> Result<Vec<Fixture>, String> {
    FIXTURES
        .iter()
        .map(|(fen, uci)| {
            let mut position = Position::from_fen(fen).map_err(|error| error.to_string())?;
            let requested = uci.parse::<UciMove>().map_err(|error| error.to_string())?;
            let current = position
                .legal_moves()
                .map_err(|error| error.to_string())?
                .iter()
                .find(|current| requested.matches(*current))
                .ok_or_else(|| format!("fixture move {uci} is not legal in {fen}"))?;
            Ok(Fixture { position, current })
        })
        .collect()
}

fn median(values: &mut [u128]) -> u128 {
    values.sort_unstable();
    values[values.len() / 2]
}

fn run() -> Result<(), String> {
    let samples = parse_samples()?;
    let fixtures = fixtures()?;
    let mut elapsed = Vec::with_capacity(samples);
    let mut maximum_allocations = 0_u64;
    let mut checksum = 0_u64;

    for sample in 0..samples {
        ALLOCATION_CALLS.store(0, Ordering::Relaxed);
        TRACK_ALLOCATIONS.store(true, Ordering::SeqCst);
        let started = Instant::now();
        let mut sample_checksum = 0_u64;
        for iteration in 0..OPERATIONS_PER_SAMPLE {
            let fixture = &fixtures[(iteration as usize) % fixtures.len()];
            let value = static_exchange_evaluation(&fixture.position, fixture.current)
                .map_err(|error| error.to_string())?;
            sample_checksum = sample_checksum
                .rotate_left(7)
                .wrapping_add(value.centipawns() as u32 as u64)
                .wrapping_add(iteration);
            black_box(value);
        }
        let elapsed_nanos = started.elapsed().as_nanos();
        TRACK_ALLOCATIONS.store(false, Ordering::SeqCst);
        let allocations = ALLOCATION_CALLS.load(Ordering::Relaxed);
        maximum_allocations = maximum_allocations.max(allocations);
        checksum = checksum
            .rotate_left(11)
            .wrapping_add(sample_checksum)
            .wrapping_add(sample as u64);
        elapsed.push(elapsed_nanos / u128::from(OPERATIONS_PER_SAMPLE));
    }

    if maximum_allocations != 0 {
        return Err(format!(
            "see.exchange allocated {maximum_allocations} times in a zero-allocation hot path"
        ));
    }

    let minimum = *elapsed.iter().min().expect("at least one sample");
    let maximum = *elapsed.iter().max().expect("at least one sample");
    let median = median(&mut elapsed);
    println!(
        "benchmark\tsamples\toperations_per_sample\tmedian_ns_per_operation\tminimum_ns_per_operation\tmaximum_ns_per_operation\tmaximum_allocations_per_sample\tchecksum\tsemantic_checksum"
    );
    println!(
        "see.exchange\t{samples}\t{OPERATIONS_PER_SAMPLE}\t{median}\t{minimum}\t{maximum}\t{maximum_allocations}\t{checksum}\t{:016x}",
        static_exchange_semantic_checksum()
    );
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("error: {error}");
            ExitCode::FAILURE
        }
    }
}
