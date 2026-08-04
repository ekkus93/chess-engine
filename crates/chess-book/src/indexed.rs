use core::{cmp::Ordering, fmt};

use chess_core::{Position, UciMove};

const MAGIC: &[u8; 8] = b"CHBKIDX\0";
const HEADER_SIZE: usize = 64;
const RECORD_SIZE: usize = 104;
const ENDIAN_MARKER: u32 = 0x0102_0304;
const MAX_POSITION_KEY_BYTES: usize = 84;
const METADATA_PRESENT: u16 = 1;
const SUPPORTED_RECORD_FLAGS: u16 = METADATA_PRESENT;

const FORMAT_VERSION_OFFSET: usize = 8;
const HEADER_SIZE_OFFSET: usize = 10;
const ENDIAN_MARKER_OFFSET: usize = 12;
const RECORD_SIZE_OFFSET: usize = 16;
const KEY_SCHEMA_VERSION_OFFSET: usize = 18;
const FLAGS_OFFSET: usize = 20;
const RECORD_COUNT_OFFSET: usize = 24;
const PAYLOAD_LENGTH_OFFSET: usize = 32;
const PAYLOAD_CHECKSUM_OFFSET: usize = 40;
const HEADER_CHECKSUM_OFFSET: usize = 44;
const HEADER_RESERVED_OFFSET: usize = 48;

const RECORD_KEY_LENGTH_OFFSET: usize = 0;
const RECORD_MOVE_LENGTH_OFFSET: usize = 1;
const RECORD_FLAGS_OFFSET: usize = 2;
const RECORD_WEIGHT_OFFSET: usize = 4;
const RECORD_METADATA_OFFSET: usize = 8;
const RECORD_KEY_OFFSET: usize = 12;
const RECORD_MOVE_OFFSET: usize = RECORD_KEY_OFFSET + MAX_POSITION_KEY_BYTES;

/// Current project-specific indexed opening-book format version.
pub const INDEXED_BOOK_FORMAT_VERSION: u16 = 1;

/// Current canonical position-key schema version.
pub const INDEXED_BOOK_KEY_SCHEMA_VERSION: u16 = 1;

/// Canonical position identity stored by the indexed book format.
///
/// Version 1 is the first four fields of canonical FEN: placement, side to
/// move, castling rights, and the FEN en-passant target. Move counters are
/// deliberately excluded.
#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct BookPositionKey(String);

impl BookPositionKey {
    /// Derives the version-1 key from a validated position.
    pub fn from_position(position: &Position) -> Result<Self, IndexedBookError> {
        let fen = position.to_fen();
        let mut fields = fen.split_whitespace();
        let mut key = String::new();
        for index in 0..4 {
            if index > 0 {
                key.push(' ');
            }
            key.push_str(
                fields
                    .next()
                    .expect("canonical six-field FEN always contains four key fields"),
            );
        }
        Self::from_canonical_text(key)
    }

    /// Returns the canonical version-1 position-key text.
    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }

    fn from_canonical_text(value: String) -> Result<Self, IndexedBookError> {
        let length = value.len();
        if length > MAX_POSITION_KEY_BYTES {
            return Err(IndexedBookError::PositionKeyTooLong {
                found: length,
                maximum: MAX_POSITION_KEY_BYTES,
            });
        }

        let full_fen = format!("{value} 0 1");
        let position = Position::from_fen(&full_fen).map_err(|error| {
            IndexedBookError::InvalidPositionKey {
                record: None,
                message: error.to_string(),
            }
        })?;
        let canonical = Self::from_position_unchecked(&position);
        if canonical != value {
            return Err(IndexedBookError::NonCanonicalPositionKey {
                record: None,
                value,
            });
        }
        Ok(Self(canonical))
    }

    fn from_record_text(record: usize, value: &str) -> Result<Self, IndexedBookError> {
        let full_fen = format!("{value} 0 1");
        let position = Position::from_fen(&full_fen).map_err(|error| {
            IndexedBookError::InvalidPositionKey {
                record: Some(record),
                message: error.to_string(),
            }
        })?;
        let canonical = Self::from_position_unchecked(&position);
        if canonical != value {
            return Err(IndexedBookError::NonCanonicalPositionKey {
                record: Some(record),
                value: value.to_owned(),
            });
        }
        Ok(Self(canonical))
    }

    fn from_position_unchecked(position: &Position) -> String {
        let fen = position.to_fen();
        fen.split_whitespace().take(4).collect::<Vec<_>>().join(" ")
    }
}

/// One raw, syntax-validated record in the project-specific indexed format.
///
/// The UCI move has not yet been resolved against generated legal moves.
/// Task 19.3 owns that legality and selection policy.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IndexedBookRecord {
    position_key: BookPositionKey,
    uci_move: UciMove,
    weight: u32,
    metadata: Option<u32>,
}

impl IndexedBookRecord {
    /// Creates a record without optional metadata.
    pub fn new(
        position: &Position,
        uci_move: UciMove,
        weight: u32,
    ) -> Result<Self, IndexedBookError> {
        Ok(Self {
            position_key: BookPositionKey::from_position(position)?,
            uci_move,
            weight,
            metadata: None,
        })
    }

    /// Creates a record with a format-defined optional 32-bit metadata value.
    pub fn with_metadata(
        position: &Position,
        uci_move: UciMove,
        weight: u32,
        metadata: u32,
    ) -> Result<Self, IndexedBookError> {
        Ok(Self {
            position_key: BookPositionKey::from_position(position)?,
            uci_move,
            weight,
            metadata: Some(metadata),
        })
    }

    /// Returns the canonical position key.
    #[must_use]
    pub const fn position_key(&self) -> &BookPositionKey {
        &self.position_key
    }

    /// Returns the unresolved UCI move syntax.
    #[must_use]
    pub const fn uci_move(&self) -> UciMove {
        self.uci_move
    }

    /// Returns the relative backend weight.
    #[must_use]
    pub const fn weight(&self) -> u32 {
        self.weight
    }

    /// Returns the optional format-defined metadata value.
    #[must_use]
    pub const fn metadata(&self) -> Option<u32> {
        self.metadata
    }
}

/// Loaded, validated project-specific indexed opening-book data.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IndexedBook {
    records: Vec<IndexedBookRecord>,
}

impl IndexedBook {
    /// Creates a canonical in-memory book, sorting records by position key and
    /// UCI move and rejecting duplicate `(position, move)` pairs.
    pub fn from_records(mut records: Vec<IndexedBookRecord>) -> Result<Self, IndexedBookError> {
        records.sort_by(compare_records);
        for pair in records.windows(2) {
            if compare_records(&pair[0], &pair[1]) == Ordering::Equal {
                return Err(IndexedBookError::DuplicateRecord {
                    position_key: pair[0].position_key.as_str().to_owned(),
                    uci_move: pair[0].uci_move.to_string(),
                });
            }
        }
        Ok(Self { records })
    }

    /// Parses and fully validates one complete in-memory book image.
    pub fn from_bytes(bytes: &[u8]) -> Result<Self, IndexedBookError> {
        if bytes.len() < HEADER_SIZE {
            return Err(IndexedBookError::TruncatedHeader { found: bytes.len() });
        }
        if &bytes[..MAGIC.len()] != MAGIC {
            return Err(IndexedBookError::InvalidMagic);
        }

        let format_version = read_u16(bytes, FORMAT_VERSION_OFFSET);
        if format_version != INDEXED_BOOK_FORMAT_VERSION {
            return Err(IndexedBookError::UnsupportedFormatVersion {
                found: format_version,
            });
        }
        let header_size = usize::from(read_u16(bytes, HEADER_SIZE_OFFSET));
        if header_size != HEADER_SIZE {
            return Err(IndexedBookError::InvalidHeaderSize { found: header_size });
        }
        let endian_marker = read_u32(bytes, ENDIAN_MARKER_OFFSET);
        if endian_marker != ENDIAN_MARKER {
            return Err(IndexedBookError::InvalidEndiannessMarker {
                found: endian_marker,
            });
        }
        let record_size = usize::from(read_u16(bytes, RECORD_SIZE_OFFSET));
        if record_size != RECORD_SIZE {
            return Err(IndexedBookError::InvalidRecordSize { found: record_size });
        }
        let key_schema_version = read_u16(bytes, KEY_SCHEMA_VERSION_OFFSET);
        if key_schema_version != INDEXED_BOOK_KEY_SCHEMA_VERSION {
            return Err(IndexedBookError::UnsupportedKeySchemaVersion {
                found: key_schema_version,
            });
        }
        let flags = read_u32(bytes, FLAGS_OFFSET);
        if flags != 0 {
            return Err(IndexedBookError::UnsupportedHeaderFlags { found: flags });
        }
        if bytes[HEADER_RESERVED_OFFSET..HEADER_SIZE]
            .iter()
            .any(|byte| *byte != 0)
        {
            return Err(IndexedBookError::NonZeroHeaderReserved);
        }

        let mut header = [0_u8; HEADER_SIZE];
        header.copy_from_slice(&bytes[..HEADER_SIZE]);
        let expected_header_checksum = read_u32(&header, HEADER_CHECKSUM_OFFSET);
        header[HEADER_CHECKSUM_OFFSET..HEADER_CHECKSUM_OFFSET + 4].fill(0);
        let actual_header_checksum = crc32(&header);
        if expected_header_checksum != actual_header_checksum {
            return Err(IndexedBookError::HeaderChecksumMismatch {
                expected: expected_header_checksum,
                actual: actual_header_checksum,
            });
        }

        let record_count_u64 = read_u64(bytes, RECORD_COUNT_OFFSET);
        let record_count = usize::try_from(record_count_u64).map_err(|_| {
            IndexedBookError::RecordCountTooLarge {
                found: record_count_u64,
            }
        })?;
        let declared_payload_u64 = read_u64(bytes, PAYLOAD_LENGTH_OFFSET);
        let declared_payload = usize::try_from(declared_payload_u64).map_err(|_| {
            IndexedBookError::PayloadLengthTooLarge {
                found: declared_payload_u64,
            }
        })?;
        let expected_payload =
            record_count
                .checked_mul(RECORD_SIZE)
                .ok_or(IndexedBookError::RecordCountTooLarge {
                    found: record_count_u64,
                })?;
        if declared_payload != expected_payload {
            return Err(IndexedBookError::DeclaredPayloadLengthMismatch {
                declared: declared_payload,
                expected: expected_payload,
            });
        }
        let actual_payload = bytes.len() - HEADER_SIZE;
        if actual_payload != declared_payload {
            return Err(IndexedBookError::FileLengthMismatch {
                declared_payload,
                actual_payload,
            });
        }

        let payload = &bytes[HEADER_SIZE..];
        let expected_payload_checksum = read_u32(bytes, PAYLOAD_CHECKSUM_OFFSET);
        let actual_payload_checksum = crc32(payload);
        if expected_payload_checksum != actual_payload_checksum {
            return Err(IndexedBookError::PayloadChecksumMismatch {
                expected: expected_payload_checksum,
                actual: actual_payload_checksum,
            });
        }

        let mut records = Vec::with_capacity(record_count);
        for (index, record_bytes) in payload.chunks_exact(RECORD_SIZE).enumerate() {
            let record = decode_record(index, record_bytes)?;
            if let Some(previous) = records.last() {
                match compare_records(previous, &record) {
                    Ordering::Less => {}
                    Ordering::Equal => {
                        return Err(IndexedBookError::DuplicateRecord {
                            position_key: record.position_key.as_str().to_owned(),
                            uci_move: record.uci_move.to_string(),
                        });
                    }
                    Ordering::Greater => {
                        return Err(IndexedBookError::UnsortedRecord { record: index });
                    }
                }
            }
            records.push(record);
        }

        Ok(Self { records })
    }

    /// Serializes the validated book as deterministic little-endian version-1 bytes.
    #[must_use]
    pub fn to_bytes(&self) -> Vec<u8> {
        let payload_length = self.records.len() * RECORD_SIZE;
        let mut bytes = vec![0_u8; HEADER_SIZE + payload_length];
        bytes[..MAGIC.len()].copy_from_slice(MAGIC);
        write_u16(
            &mut bytes,
            FORMAT_VERSION_OFFSET,
            INDEXED_BOOK_FORMAT_VERSION,
        );
        write_u16(
            &mut bytes,
            HEADER_SIZE_OFFSET,
            u16::try_from(HEADER_SIZE).expect("header size fits u16"),
        );
        write_u32(&mut bytes, ENDIAN_MARKER_OFFSET, ENDIAN_MARKER);
        write_u16(
            &mut bytes,
            RECORD_SIZE_OFFSET,
            u16::try_from(RECORD_SIZE).expect("record size fits u16"),
        );
        write_u16(
            &mut bytes,
            KEY_SCHEMA_VERSION_OFFSET,
            INDEXED_BOOK_KEY_SCHEMA_VERSION,
        );
        write_u64(
            &mut bytes,
            RECORD_COUNT_OFFSET,
            u64::try_from(self.records.len()).expect("record count fits u64"),
        );
        write_u64(
            &mut bytes,
            PAYLOAD_LENGTH_OFFSET,
            u64::try_from(payload_length).expect("payload length fits u64"),
        );

        for (index, record) in self.records.iter().enumerate() {
            let start = HEADER_SIZE + index * RECORD_SIZE;
            encode_record(record, &mut bytes[start..start + RECORD_SIZE]);
        }

        let payload_checksum = crc32(&bytes[HEADER_SIZE..]);
        write_u32(&mut bytes, PAYLOAD_CHECKSUM_OFFSET, payload_checksum);
        let header_checksum = crc32(&bytes[..HEADER_SIZE]);
        write_u32(&mut bytes, HEADER_CHECKSUM_OFFSET, header_checksum);
        bytes
    }

    /// Returns all records in canonical `(position key, UCI move)` order.
    #[must_use]
    pub fn records(&self) -> &[IndexedBookRecord] {
        &self.records
    }

    /// Returns whether this book contains no records.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.records.is_empty()
    }

    /// Returns the number of records.
    #[must_use]
    pub fn len(&self) -> usize {
        self.records.len()
    }

    /// Returns the contiguous indexed record range for a validated position.
    pub fn records_for_position(
        &self,
        position: &Position,
    ) -> Result<&[IndexedBookRecord], IndexedBookError> {
        let key = BookPositionKey::from_position(position)?;
        let start = self
            .records
            .partition_point(|record| record.position_key < key);
        let end = self
            .records
            .partition_point(|record| record.position_key <= key);
        Ok(&self.records[start..end])
    }
}

/// Structured format, schema, checksum, and record validation failure.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum IndexedBookError {
    /// The input is shorter than the fixed header.
    TruncatedHeader { found: usize },
    /// The eight-byte magic does not identify this format.
    InvalidMagic,
    /// The file declares an unsupported format version.
    UnsupportedFormatVersion { found: u16 },
    /// The fixed header size is incompatible.
    InvalidHeaderSize { found: usize },
    /// The little-endian marker is absent or byte-swapped.
    InvalidEndiannessMarker { found: u32 },
    /// The fixed record size is incompatible.
    InvalidRecordSize { found: usize },
    /// The canonical position-key schema is unsupported.
    UnsupportedKeySchemaVersion { found: u16 },
    /// Reserved header flags are nonzero.
    UnsupportedHeaderFlags { found: u32 },
    /// Reserved header bytes are nonzero.
    NonZeroHeaderReserved,
    /// The header checksum does not match.
    HeaderChecksumMismatch { expected: u32, actual: u32 },
    /// The record count cannot be represented or multiplied safely.
    RecordCountTooLarge { found: u64 },
    /// The payload length cannot be represented on this platform.
    PayloadLengthTooLarge { found: u64 },
    /// Header record count and declared payload length disagree.
    DeclaredPayloadLengthMismatch { declared: usize, expected: usize },
    /// The actual file length disagrees with the declared payload length.
    FileLengthMismatch {
        declared_payload: usize,
        actual_payload: usize,
    },
    /// The payload checksum does not match.
    PayloadChecksumMismatch { expected: u32, actual: u32 },
    /// A canonical position key exceeded the fixed schema bound.
    PositionKeyTooLong { found: usize, maximum: usize },
    /// A record has an invalid position-key length.
    InvalidPositionKeyLength { record: usize, found: usize },
    /// A record position key is not UTF-8.
    InvalidPositionKeyUtf8 { record: usize },
    /// A record position key is not valid canonical four-field FEN identity.
    InvalidPositionKey {
        record: Option<usize>,
        message: String,
    },
    /// A valid position key was not encoded canonically.
    NonCanonicalPositionKey {
        record: Option<usize>,
        value: String,
    },
    /// A record has an invalid UCI move length.
    InvalidMoveLength { record: usize, found: usize },
    /// A record UCI move is not UTF-8.
    InvalidMoveUtf8 { record: usize },
    /// A record UCI move has invalid coordinate syntax.
    InvalidMove { record: usize, message: String },
    /// A record uses unsupported flag bits.
    UnsupportedRecordFlags { record: usize, found: u16 },
    /// An absent metadata flag had a nonzero metadata word.
    MetadataWithoutFlag { record: usize },
    /// Fixed-width key or move padding was not zero.
    NonZeroRecordPadding { record: usize },
    /// Records are not in canonical ascending index order.
    UnsortedRecord { record: usize },
    /// More than one record uses the same position and move.
    DuplicateRecord {
        position_key: String,
        uci_move: String,
    },
}

impl fmt::Display for IndexedBookError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::TruncatedHeader { found } => {
                write!(formatter, "opening-book header is truncated: {found} bytes")
            }
            Self::InvalidMagic => formatter.write_str("invalid opening-book magic"),
            Self::UnsupportedFormatVersion { found } => {
                write!(formatter, "unsupported opening-book format version {found}")
            }
            Self::InvalidHeaderSize { found } => {
                write!(formatter, "invalid opening-book header size {found}")
            }
            Self::InvalidEndiannessMarker { found } => {
                write!(formatter, "invalid opening-book endianness marker {found:#010x}")
            }
            Self::InvalidRecordSize { found } => {
                write!(formatter, "invalid opening-book record size {found}")
            }
            Self::UnsupportedKeySchemaVersion { found } => {
                write!(formatter, "unsupported opening-book key schema version {found}")
            }
            Self::UnsupportedHeaderFlags { found } => {
                write!(formatter, "unsupported opening-book header flags {found:#010x}")
            }
            Self::NonZeroHeaderReserved => {
                formatter.write_str("opening-book reserved header bytes are nonzero")
            }
            Self::HeaderChecksumMismatch { expected, actual } => write!(
                formatter,
                "opening-book header checksum mismatch: expected {expected:#010x}, actual {actual:#010x}"
            ),
            Self::RecordCountTooLarge { found } => {
                write!(formatter, "opening-book record count is too large: {found}")
            }
            Self::PayloadLengthTooLarge { found } => {
                write!(formatter, "opening-book payload length is too large: {found}")
            }
            Self::DeclaredPayloadLengthMismatch { declared, expected } => write!(
                formatter,
                "opening-book declared payload length {declared} does not match {expected}"
            ),
            Self::FileLengthMismatch {
                declared_payload,
                actual_payload,
            } => write!(
                formatter,
                "opening-book payload length mismatch: declared {declared_payload}, actual {actual_payload}"
            ),
            Self::PayloadChecksumMismatch { expected, actual } => write!(
                formatter,
                "opening-book payload checksum mismatch: expected {expected:#010x}, actual {actual:#010x}"
            ),
            Self::PositionKeyTooLong { found, maximum } => write!(
                formatter,
                "opening-book position key is {found} bytes, maximum is {maximum}"
            ),
            Self::InvalidPositionKeyLength { record, found } => write!(
                formatter,
                "opening-book record {record} has invalid position-key length {found}"
            ),
            Self::InvalidPositionKeyUtf8 { record } => {
                write!(formatter, "opening-book record {record} position key is not UTF-8")
            }
            Self::InvalidPositionKey { record, message } => match record {
                Some(record) => write!(
                    formatter,
                    "opening-book record {record} has invalid position key: {message}"
                ),
                None => write!(formatter, "invalid opening-book position key: {message}"),
            },
            Self::NonCanonicalPositionKey { record, value } => match record {
                Some(record) => write!(
                    formatter,
                    "opening-book record {record} has noncanonical position key {value:?}"
                ),
                None => write!(formatter, "noncanonical opening-book position key {value:?}"),
            },
            Self::InvalidMoveLength { record, found } => write!(
                formatter,
                "opening-book record {record} has invalid move length {found}"
            ),
            Self::InvalidMoveUtf8 { record } => {
                write!(formatter, "opening-book record {record} move is not UTF-8")
            }
            Self::InvalidMove { record, message } => {
                write!(formatter, "opening-book record {record} has invalid move: {message}")
            }
            Self::UnsupportedRecordFlags { record, found } => write!(
                formatter,
                "opening-book record {record} has unsupported flags {found:#06x}"
            ),
            Self::MetadataWithoutFlag { record } => write!(
                formatter,
                "opening-book record {record} has metadata without its presence flag"
            ),
            Self::NonZeroRecordPadding { record } => {
                write!(formatter, "opening-book record {record} has nonzero padding")
            }
            Self::UnsortedRecord { record } => {
                write!(formatter, "opening-book record {record} is out of index order")
            }
            Self::DuplicateRecord {
                position_key,
                uci_move,
            } => write!(
                formatter,
                "duplicate opening-book record for {position_key:?} and {uci_move}"
            ),
        }
    }
}

impl std::error::Error for IndexedBookError {}

fn compare_records(left: &IndexedBookRecord, right: &IndexedBookRecord) -> Ordering {
    left.position_key
        .cmp(&right.position_key)
        .then_with(|| left.uci_move.cmp(&right.uci_move))
}

fn decode_record(index: usize, bytes: &[u8]) -> Result<IndexedBookRecord, IndexedBookError> {
    let key_length = usize::from(bytes[RECORD_KEY_LENGTH_OFFSET]);
    if !(1..=MAX_POSITION_KEY_BYTES).contains(&key_length) {
        return Err(IndexedBookError::InvalidPositionKeyLength {
            record: index,
            found: key_length,
        });
    }
    let move_length = usize::from(bytes[RECORD_MOVE_LENGTH_OFFSET]);
    if !(4..=5).contains(&move_length) {
        return Err(IndexedBookError::InvalidMoveLength {
            record: index,
            found: move_length,
        });
    }
    let flags = read_u16(bytes, RECORD_FLAGS_OFFSET);
    if flags & !SUPPORTED_RECORD_FLAGS != 0 {
        return Err(IndexedBookError::UnsupportedRecordFlags {
            record: index,
            found: flags,
        });
    }
    let weight = read_u32(bytes, RECORD_WEIGHT_OFFSET);
    let metadata_value = read_u32(bytes, RECORD_METADATA_OFFSET);
    let metadata = if flags & METADATA_PRESENT != 0 {
        Some(metadata_value)
    } else {
        if metadata_value != 0 {
            return Err(IndexedBookError::MetadataWithoutFlag { record: index });
        }
        None
    };

    let key_end = RECORD_KEY_OFFSET + key_length;
    let move_end = RECORD_MOVE_OFFSET + move_length;
    if bytes[key_end..RECORD_MOVE_OFFSET]
        .iter()
        .chain(bytes[move_end..RECORD_SIZE].iter())
        .any(|byte| *byte != 0)
    {
        return Err(IndexedBookError::NonZeroRecordPadding { record: index });
    }

    let key_text = core::str::from_utf8(&bytes[RECORD_KEY_OFFSET..key_end])
        .map_err(|_| IndexedBookError::InvalidPositionKeyUtf8 { record: index })?;
    let position_key = BookPositionKey::from_record_text(index, key_text)?;
    let move_text = core::str::from_utf8(&bytes[RECORD_MOVE_OFFSET..move_end])
        .map_err(|_| IndexedBookError::InvalidMoveUtf8 { record: index })?;
    let uci_move = move_text
        .parse::<UciMove>()
        .map_err(|error| IndexedBookError::InvalidMove {
            record: index,
            message: error.to_string(),
        })?;

    Ok(IndexedBookRecord {
        position_key,
        uci_move,
        weight,
        metadata,
    })
}

fn encode_record(record: &IndexedBookRecord, bytes: &mut [u8]) {
    let key = record.position_key.as_str().as_bytes();
    let uci_move = record.uci_move.to_string();
    let move_bytes = uci_move.as_bytes();
    bytes[RECORD_KEY_LENGTH_OFFSET] =
        u8::try_from(key.len()).expect("validated position key length fits u8");
    bytes[RECORD_MOVE_LENGTH_OFFSET] =
        u8::try_from(move_bytes.len()).expect("UCI move length fits u8");
    if let Some(metadata) = record.metadata {
        write_u16(bytes, RECORD_FLAGS_OFFSET, METADATA_PRESENT);
        write_u32(bytes, RECORD_METADATA_OFFSET, metadata);
    }
    write_u32(bytes, RECORD_WEIGHT_OFFSET, record.weight);
    bytes[RECORD_KEY_OFFSET..RECORD_KEY_OFFSET + key.len()].copy_from_slice(key);
    bytes[RECORD_MOVE_OFFSET..RECORD_MOVE_OFFSET + move_bytes.len()].copy_from_slice(move_bytes);
}

fn crc32(bytes: &[u8]) -> u32 {
    let mut crc = u32::MAX;
    for byte in bytes {
        crc ^= u32::from(*byte);
        for _ in 0..8 {
            let mask = 0_u32.wrapping_sub(crc & 1);
            crc = (crc >> 1) ^ (0xedb8_8320 & mask);
        }
    }
    !crc
}

fn read_u16(bytes: &[u8], offset: usize) -> u16 {
    u16::from_le_bytes(
        bytes[offset..offset + 2]
            .try_into()
            .expect("fixed-width u16 field is in bounds"),
    )
}

fn read_u32(bytes: &[u8], offset: usize) -> u32 {
    u32::from_le_bytes(
        bytes[offset..offset + 4]
            .try_into()
            .expect("fixed-width u32 field is in bounds"),
    )
}

fn read_u64(bytes: &[u8], offset: usize) -> u64 {
    u64::from_le_bytes(
        bytes[offset..offset + 8]
            .try_into()
            .expect("fixed-width u64 field is in bounds"),
    )
}

fn write_u16(bytes: &mut [u8], offset: usize, value: u16) {
    bytes[offset..offset + 2].copy_from_slice(&value.to_le_bytes());
}

fn write_u32(bytes: &mut [u8], offset: usize, value: u32) {
    bytes[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}

fn write_u64(bytes: &mut [u8], offset: usize, value: u64) {
    bytes[offset..offset + 8].copy_from_slice(&value.to_le_bytes());
}

#[cfg(test)]
mod tests {
    use super::*;

    fn record(position: &Position, uci_move: &str, weight: u32) -> IndexedBookRecord {
        IndexedBookRecord::new(
            position,
            uci_move.parse().expect("test move syntax is valid"),
            weight,
        )
        .expect("test position key is valid")
    }

    fn rewrite_checksums(bytes: &mut [u8]) {
        let payload_checksum = crc32(&bytes[HEADER_SIZE..]);
        write_u32(bytes, PAYLOAD_CHECKSUM_OFFSET, payload_checksum);
        write_u32(bytes, HEADER_CHECKSUM_OFFSET, 0);
        let header_checksum = crc32(&bytes[..HEADER_SIZE]);
        write_u32(bytes, HEADER_CHECKSUM_OFFSET, header_checksum);
    }

    #[test]
    fn version_one_round_trips_in_canonical_index_order() {
        let starting = Position::starting();
        let after_e4 =
            Position::from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
                .expect("test FEN is valid");
        let records = vec![
            record(&starting, "e2e4", 20),
            IndexedBookRecord::with_metadata(
                &after_e4,
                "c7c5".parse().expect("test move syntax is valid"),
                8,
                17,
            )
            .expect("test position key is valid"),
            record(&starting, "d2d4", 30),
        ];

        let book = IndexedBook::from_records(records).expect("records are unique");
        let encoded = book.to_bytes();
        let decoded = IndexedBook::from_bytes(&encoded).expect("encoded book is valid");
        assert_eq!(decoded, book);
        assert_eq!(decoded.to_bytes(), encoded);

        let starting_records = decoded
            .records_for_position(&starting)
            .expect("position key is valid");
        assert_eq!(starting_records.len(), 2);
        assert_eq!(starting_records[0].uci_move().to_string(), "d2d4");
        assert_eq!(starting_records[1].uci_move().to_string(), "e2e4");
        assert_eq!(
            decoded
                .records_for_position(&after_e4)
                .expect("position key is valid")[0]
                .metadata(),
            Some(17)
        );
    }

    #[test]
    fn header_declares_version_schema_and_little_endian_layout() {
        let book =
            IndexedBook::from_records(vec![record(&Position::starting(), "e2e4", 0x1122_3344)])
                .expect("record is valid");
        let bytes = book.to_bytes();

        assert_eq!(&bytes[..8], MAGIC);
        assert_eq!(read_u16(&bytes, FORMAT_VERSION_OFFSET), 1);
        assert_eq!(read_u16(&bytes, KEY_SCHEMA_VERSION_OFFSET), 1);
        assert_eq!(read_u32(&bytes, ENDIAN_MARKER_OFFSET), 0x0102_0304);
        assert_eq!(
            read_u32(&bytes, HEADER_SIZE + RECORD_WEIGHT_OFFSET),
            0x1122_3344
        );
    }

    #[test]
    fn checksum_corruption_is_rejected_before_record_use() {
        let book = IndexedBook::from_records(vec![record(&Position::starting(), "e2e4", 9)])
            .expect("record is valid");
        let mut bytes = book.to_bytes();
        let final_index = bytes.len() - 1;
        bytes[final_index] ^= 1;

        assert!(matches!(
            IndexedBook::from_bytes(&bytes),
            Err(IndexedBookError::PayloadChecksumMismatch { .. })
        ));
    }

    #[test]
    fn incompatible_header_schema_is_rejected_loudly() {
        let book = IndexedBook::from_records(Vec::new()).expect("empty book is valid");

        let mut version = book.to_bytes();
        write_u16(&mut version, FORMAT_VERSION_OFFSET, 2);
        rewrite_checksums(&mut version);
        assert_eq!(
            IndexedBook::from_bytes(&version),
            Err(IndexedBookError::UnsupportedFormatVersion { found: 2 })
        );

        let mut endian = book.to_bytes();
        write_u32(
            &mut endian,
            ENDIAN_MARKER_OFFSET,
            ENDIAN_MARKER.swap_bytes(),
        );
        rewrite_checksums(&mut endian);
        assert!(matches!(
            IndexedBook::from_bytes(&endian),
            Err(IndexedBookError::InvalidEndiannessMarker { .. })
        ));

        let mut schema = book.to_bytes();
        write_u16(&mut schema, KEY_SCHEMA_VERSION_OFFSET, 7);
        rewrite_checksums(&mut schema);
        assert_eq!(
            IndexedBook::from_bytes(&schema),
            Err(IndexedBookError::UnsupportedKeySchemaVersion { found: 7 })
        );
    }

    #[test]
    fn structurally_corrupt_records_are_rejected_after_valid_checksum() {
        let book = IndexedBook::from_records(vec![record(&Position::starting(), "e2e4", 9)])
            .expect("record is valid");
        let mut bytes = book.to_bytes();
        let move_start = HEADER_SIZE + RECORD_MOVE_OFFSET;
        bytes[move_start..move_start + 4].copy_from_slice(b"z9z9");
        rewrite_checksums(&mut bytes);

        assert!(matches!(
            IndexedBook::from_bytes(&bytes),
            Err(IndexedBookError::InvalidMove { record: 0, .. })
        ));
    }

    #[test]
    fn duplicate_position_move_pairs_are_rejected() {
        let starting = Position::starting();
        let first = record(&starting, "e2e4", 1);
        let second = record(&starting, "e2e4", 2);

        assert!(matches!(
            IndexedBook::from_records(vec![first, second]),
            Err(IndexedBookError::DuplicateRecord { .. })
        ));
    }

    #[test]
    fn declared_and_actual_lengths_must_match_exactly() {
        let book = IndexedBook::from_records(Vec::new()).expect("empty book is valid");
        let mut bytes = book.to_bytes();
        bytes.push(0);

        assert_eq!(
            IndexedBook::from_bytes(&bytes),
            Err(IndexedBookError::FileLengthMismatch {
                declared_payload: 0,
                actual_payload: 1,
            })
        );
    }
}
