use std::{
    cell::RefCell,
    collections::HashMap,
    panic::{catch_unwind, AssertUnwindSafe},
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc, Mutex, MutexGuard, OnceLock,
    },
};

use crate::{Engine, SearchCancellationHandle};

use super::types::{
    ChessEngineBuffer, ChessEngineCancellationHandle, ChessEngineHandle, ChessEngineResultCode,
};

const HANDLE_TAG_MASK: u64 = 0b11;
const ENGINE_HANDLE_TAG: u64 = 0b01;
const CANCELLATION_HANDLE_TAG: u64 = 0b10;
const BUFFER_HANDLE_TAG: u64 = 0b11;
const MAX_HANDLE_SEQUENCE: u64 = u64::MAX >> 2;

static NEXT_HANDLE_SEQUENCE: AtomicU64 = AtomicU64::new(1);

type EngineEntry = Arc<Mutex<Engine>>;
type EngineRegistry = HashMap<ChessEngineHandle, EngineEntry>;
type CancellationEntry = Arc<SearchCancellationHandle>;
type CancellationRegistry = HashMap<ChessEngineCancellationHandle, CancellationEntry>;
type BufferRegistry = HashMap<u64, Box<[u8]>>;

static ENGINES: OnceLock<Mutex<EngineRegistry>> = OnceLock::new();
static CANCELLATIONS: OnceLock<Mutex<CancellationRegistry>> = OnceLock::new();
static BUFFERS: OnceLock<Mutex<BufferRegistry>> = OnceLock::new();

thread_local! {
    static LAST_ERROR: RefCell<Vec<u8>> = const { RefCell::new(Vec::new()) };
}

pub(crate) type AbiResult<T> = Result<T, AbiFailure>;

#[derive(Debug)]
pub(crate) struct AbiFailure {
    code: ChessEngineResultCode,
    message: String,
}

impl AbiFailure {
    pub(crate) fn new(code: ChessEngineResultCode, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
        }
    }

    pub(crate) const fn code(&self) -> ChessEngineResultCode {
        self.code
    }

    pub(crate) fn message(&self) -> &str {
        &self.message
    }
}

pub(crate) fn boundary(operation: impl FnOnce() -> AbiResult<()>) -> ChessEngineResultCode {
    match catch_unwind(AssertUnwindSafe(operation)) {
        Ok(Ok(())) => {
            clear_last_error();
            ChessEngineResultCode::Ok
        }
        Ok(Err(error)) => {
            replace_last_error(error.message().as_bytes().to_vec());
            error.code()
        }
        Err(_) => {
            replace_last_error(b"Rust panic contained at the chess engine C ABI boundary".to_vec());
            ChessEngineResultCode::Panic
        }
    }
}

pub(crate) fn boundary_preserving_error(
    operation: impl FnOnce() -> AbiResult<()>,
) -> ChessEngineResultCode {
    match catch_unwind(AssertUnwindSafe(operation)) {
        Ok(Ok(())) => ChessEngineResultCode::Ok,
        Ok(Err(error)) => {
            replace_last_error(error.message().as_bytes().to_vec());
            error.code()
        }
        Err(_) => {
            replace_last_error(b"Rust panic contained at the chess engine C ABI boundary".to_vec());
            ChessEngineResultCode::Panic
        }
    }
}

pub(crate) fn scalar_boundary(operation: impl FnOnce() -> u32) -> u32 {
    match catch_unwind(AssertUnwindSafe(operation)) {
        Ok(value) => {
            clear_last_error();
            value
        }
        Err(_) => {
            replace_last_error(b"Rust panic contained at the chess engine C ABI boundary".to_vec());
            0
        }
    }
}

pub(crate) fn last_error_bytes() -> Vec<u8> {
    LAST_ERROR.with(|slot| slot.borrow().clone())
}

fn clear_last_error() {
    replace_last_error(Vec::new());
}

fn replace_last_error(bytes: Vec<u8>) {
    let _ = catch_unwind(AssertUnwindSafe(|| {
        LAST_ERROR.with(|slot| {
            *slot.borrow_mut() = bytes;
        });
    }));
}

fn next_token(tag: u64) -> AbiResult<u64> {
    let sequence = NEXT_HANDLE_SEQUENCE
        .fetch_update(Ordering::Relaxed, Ordering::Relaxed, |current| {
            if current > MAX_HANDLE_SEQUENCE {
                None
            } else {
                current.checked_add(1)
            }
        })
        .map_err(|_| {
            AbiFailure::new(
                ChessEngineResultCode::InternalError,
                "opaque C ABI handle space is exhausted",
            )
        })?;
    Ok((sequence << 2) | tag)
}

fn validate_token(token: u64, expected_tag: u64, label: &str) -> AbiResult<()> {
    if token == 0 {
        return Err(AbiFailure::new(
            ChessEngineResultCode::NullPointer,
            format!("{label} is null"),
        ));
    }
    if token & HANDLE_TAG_MASK != expected_tag {
        return Err(AbiFailure::new(
            ChessEngineResultCode::InvalidHandle,
            format!("{label} has the wrong opaque handle type"),
        ));
    }
    Ok(())
}

fn engine_registry() -> &'static Mutex<EngineRegistry> {
    ENGINES.get_or_init(|| Mutex::new(HashMap::new()))
}

fn cancellation_registry() -> &'static Mutex<CancellationRegistry> {
    CANCELLATIONS.get_or_init(|| Mutex::new(HashMap::new()))
}

fn buffer_registry() -> &'static Mutex<BufferRegistry> {
    BUFFERS.get_or_init(|| Mutex::new(HashMap::new()))
}

fn lock_engine_registry() -> AbiResult<MutexGuard<'static, EngineRegistry>> {
    engine_registry().lock().map_err(|_| {
        AbiFailure::new(
            ChessEngineResultCode::InternalError,
            "engine handle registry lock is poisoned",
        )
    })
}

fn lock_cancellation_registry() -> AbiResult<MutexGuard<'static, CancellationRegistry>> {
    cancellation_registry().lock().map_err(|_| {
        AbiFailure::new(
            ChessEngineResultCode::InternalError,
            "cancellation handle registry lock is poisoned",
        )
    })
}

fn lock_buffer_registry() -> AbiResult<MutexGuard<'static, BufferRegistry>> {
    buffer_registry().lock().map_err(|_| {
        AbiFailure::new(
            ChessEngineResultCode::InternalError,
            "output buffer registry lock is poisoned",
        )
    })
}

pub(crate) fn insert_engine(engine: Engine) -> AbiResult<ChessEngineHandle> {
    let token = next_token(ENGINE_HANDLE_TAG)?;
    let mut entries = lock_engine_registry()?;
    entries.try_reserve(1).map_err(|error| {
        AbiFailure::new(
            ChessEngineResultCode::AllocationFailure,
            format!("failed to reserve engine handle registry entry: {error}"),
        )
    })?;
    entries.insert(token, Arc::new(Mutex::new(engine)));
    Ok(token)
}

pub(crate) fn resolve_engine(handle: ChessEngineHandle) -> AbiResult<EngineEntry> {
    validate_token(handle, ENGINE_HANDLE_TAG, "engine handle")?;
    let entries = lock_engine_registry()?;
    entries.get(&handle).cloned().ok_or_else(|| {
        AbiFailure::new(
            ChessEngineResultCode::InvalidHandle,
            "engine handle is unknown or has already been destroyed",
        )
    })
}

pub(crate) fn remove_engine(handle: ChessEngineHandle) -> AbiResult<()> {
    validate_token(handle, ENGINE_HANDLE_TAG, "engine handle")?;
    let mut entries = lock_engine_registry()?;
    entries.remove(&handle).map(|_| ()).ok_or_else(|| {
        AbiFailure::new(
            ChessEngineResultCode::InvalidHandle,
            "engine handle is unknown or has already been destroyed",
        )
    })
}

pub(crate) fn lock_engine(entry: &EngineEntry) -> AbiResult<MutexGuard<'_, Engine>> {
    entry.lock().map_err(|_| {
        AbiFailure::new(
            ChessEngineResultCode::InternalError,
            "engine instance lock is poisoned",
        )
    })
}

pub(crate) fn insert_cancellation(
    cancellation: SearchCancellationHandle,
) -> AbiResult<ChessEngineCancellationHandle> {
    let token = next_token(CANCELLATION_HANDLE_TAG)?;
    let mut entries = lock_cancellation_registry()?;
    entries.try_reserve(1).map_err(|error| {
        AbiFailure::new(
            ChessEngineResultCode::AllocationFailure,
            format!("failed to reserve cancellation handle registry entry: {error}"),
        )
    })?;
    entries.insert(token, Arc::new(cancellation));
    Ok(token)
}

pub(crate) fn resolve_cancellation(
    handle: ChessEngineCancellationHandle,
) -> AbiResult<CancellationEntry> {
    validate_token(handle, CANCELLATION_HANDLE_TAG, "cancellation handle")?;
    let entries = lock_cancellation_registry()?;
    entries.get(&handle).cloned().ok_or_else(|| {
        AbiFailure::new(
            ChessEngineResultCode::InvalidHandle,
            "cancellation handle is unknown or has already been destroyed",
        )
    })
}

pub(crate) fn remove_cancellation(handle: ChessEngineCancellationHandle) -> AbiResult<()> {
    validate_token(handle, CANCELLATION_HANDLE_TAG, "cancellation handle")?;
    let mut entries = lock_cancellation_registry()?;
    entries.remove(&handle).map(|_| ()).ok_or_else(|| {
        AbiFailure::new(
            ChessEngineResultCode::InvalidHandle,
            "cancellation handle is unknown or has already been destroyed",
        )
    })
}

pub(crate) fn allocate_buffer(bytes: Vec<u8>) -> AbiResult<ChessEngineBuffer> {
    if bytes.is_empty() {
        return Ok(ChessEngineBuffer::empty());
    }

    let token = next_token(BUFFER_HANDLE_TAG)?;
    let allocation = bytes.into_boxed_slice();
    let data = allocation.as_ptr();
    let len = allocation.len();
    let mut entries = lock_buffer_registry()?;
    entries.try_reserve(1).map_err(|error| {
        AbiFailure::new(
            ChessEngineResultCode::AllocationFailure,
            format!("failed to reserve output buffer registry entry: {error}"),
        )
    })?;
    entries.insert(token, allocation);
    Ok(ChessEngineBuffer {
        data,
        len,
        allocation: token,
    })
}

pub(crate) fn release_buffers(buffers: &[ChessEngineBuffer]) -> AbiResult<()> {
    let mut entries = lock_buffer_registry()?;

    for (index, buffer) in buffers.iter().enumerate() {
        if buffer.allocation == 0 {
            if !buffer.data.is_null() || buffer.len != 0 {
                return Err(AbiFailure::new(
                    ChessEngineResultCode::InvalidBuffer,
                    "empty output buffer has nonempty pointer or length fields",
                ));
            }
            continue;
        }

        validate_token(buffer.allocation, BUFFER_HANDLE_TAG, "buffer allocation")?;
        if buffers[..index]
            .iter()
            .any(|previous| previous.allocation == buffer.allocation)
        {
            return Err(AbiFailure::new(
                ChessEngineResultCode::InvalidBuffer,
                "the same output allocation appears more than once",
            ));
        }

        let allocation = entries.get(&buffer.allocation).ok_or_else(|| {
            AbiFailure::new(
                ChessEngineResultCode::InvalidBuffer,
                "output buffer is unknown or has already been freed",
            )
        })?;
        if allocation.len() != buffer.len || allocation.as_ptr() != buffer.data {
            return Err(AbiFailure::new(
                ChessEngineResultCode::InvalidBuffer,
                "output buffer pointer or length does not match its allocation token",
            ));
        }
    }

    for buffer in buffers {
        if buffer.allocation != 0 {
            entries.remove(&buffer.allocation);
        }
    }
    Ok(())
}

#[cfg(test)]
pub(crate) fn force_boundary_panic_for_test() -> ChessEngineResultCode {
    boundary(|| -> AbiResult<()> { panic!("injected boundary panic") })
}
