#ifndef CHESS_ENGINE_H
#define CHESS_ENGINE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CHESS_ENGINE_ABI_VERSION UINT32_C(1)

#define CHESS_ENGINE_NULL_HANDLE UINT64_C(0)
#define CHESS_ENGINE_NULL_CANCELLATION_HANDLE UINT64_C(0)

#define CHESS_ENGINE_SEARCH_FLAG_DEPTH (UINT32_C(1) << 0)
#define CHESS_ENGINE_SEARCH_FLAG_NODES (UINT32_C(1) << 1)
#define CHESS_ENGINE_SEARCH_FLAG_SOFT_TIME (UINT32_C(1) << 2)
#define CHESS_ENGINE_SEARCH_FLAG_HARD_TIME (UINT32_C(1) << 3)
#define CHESS_ENGINE_SEARCH_FLAG_INFINITE (UINT32_C(1) << 4)
#define CHESS_ENGINE_SEARCH_FLAG_CHECK_EXTENSION (UINT32_C(1) << 5)
#define CHESS_ENGINE_SEARCH_FLAG_CANCELLATION (UINT32_C(1) << 6)

typedef uint64_t ChessEngineHandle;
typedef uint64_t ChessEngineCancellationHandle;
typedef int32_t ChessEngineResultCode;
typedef int32_t ChessEngineColor;
typedef int32_t ChessEngineGameStatusKind;
typedef int32_t ChessEngineDrawReason;
typedef int32_t ChessEngineScoreKind;
typedef int32_t ChessEngineSearchTerminationKind;
typedef int32_t ChessEngineSearchFallbackKind;

enum {
    CHESS_ENGINE_RESULT_OK = 0,
    CHESS_ENGINE_RESULT_NULL_POINTER = 1,
    CHESS_ENGINE_RESULT_INVALID_HANDLE = 2,
    CHESS_ENGINE_RESULT_INVALID_UTF8 = 3,
    CHESS_ENGINE_RESULT_INVALID_ARGUMENT = 4,
    CHESS_ENGINE_RESULT_ABI_MISMATCH = 5,
    CHESS_ENGINE_RESULT_INVALID_FEN = 10,
    CHESS_ENGINE_RESULT_INVALID_MOVE_SYNTAX = 11,
    CHESS_ENGINE_RESULT_ILLEGAL_MOVE = 12,
    CHESS_ENGINE_RESULT_GAME_OVER = 13,
    CHESS_ENGINE_RESULT_GAME_ERROR = 14,
    CHESS_ENGINE_RESULT_INVALID_WEIGHT_SET = 15,
    CHESS_ENGINE_RESULT_INVALID_OPENING_BOOK = 16,
    CHESS_ENGINE_RESULT_SEARCH_ERROR = 20,
    CHESS_ENGINE_RESULT_OPENING_BOOK_ERROR = 21,
    CHESS_ENGINE_RESULT_ALLOCATION_FAILURE = 30,
    CHESS_ENGINE_RESULT_INVALID_BUFFER = 31,
    CHESS_ENGINE_RESULT_INTERNAL_ERROR = 100,
    CHESS_ENGINE_RESULT_PANIC = 101
};

enum {
    CHESS_ENGINE_COLOR_NONE = 0,
    CHESS_ENGINE_COLOR_WHITE = 1,
    CHESS_ENGINE_COLOR_BLACK = 2
};

enum {
    CHESS_ENGINE_STATUS_ONGOING = 0,
    CHESS_ENGINE_STATUS_CHECKMATE = 1,
    CHESS_ENGINE_STATUS_STALEMATE = 2,
    CHESS_ENGINE_STATUS_AUTOMATIC_DRAW = 3,
    CHESS_ENGINE_STATUS_CLAIMABLE_DRAW = 4
};

enum {
    CHESS_ENGINE_DRAW_NONE = 0,
    CHESS_ENGINE_DRAW_THREEFOLD_REPETITION = 1,
    CHESS_ENGINE_DRAW_FIVEFOLD_REPETITION = 2,
    CHESS_ENGINE_DRAW_FIFTY_MOVE_RULE = 3,
    CHESS_ENGINE_DRAW_SEVENTY_FIVE_MOVE_RULE = 4,
    CHESS_ENGINE_DRAW_DEAD_POSITION = 5
};

enum {
    CHESS_ENGINE_SCORE_NONE = 0,
    CHESS_ENGINE_SCORE_CENTIPAWNS = 1,
    CHESS_ENGINE_SCORE_MATE = 2
};

enum {
    CHESS_ENGINE_TERMINATION_NONE = 0,
    CHESS_ENGINE_TERMINATION_DEPTH = 1,
    CHESS_ENGINE_TERMINATION_NODES = 2,
    CHESS_ENGINE_TERMINATION_SOFT_TIME = 3,
    CHESS_ENGINE_TERMINATION_HARD_TIME = 4,
    CHESS_ENGINE_TERMINATION_EXPLICIT_STOP = 5,
    CHESS_ENGINE_TERMINATION_MAXIMUM_SUPPORTED_DEPTH = 6
};

enum {
    CHESS_ENGINE_FALLBACK_NONE = 0,
    CHESS_ENGINE_FALLBACK_FIRST_LEGAL_MOVE = 1,
    CHESS_ENGINE_FALLBACK_NO_LEGAL_MOVE = 2
};

typedef struct ChessEngineConfig {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t transposition_table_mebibytes;
} ChessEngineConfig;

typedef struct ChessEngineBuffer {
    const uint8_t *data;
    size_t len;
    uint64_t allocation;
} ChessEngineBuffer;

typedef struct ChessEngineGameStatus {
    uint32_t struct_size;
    uint32_t abi_version;
    ChessEngineGameStatusKind kind;
    ChessEngineColor winner;
    ChessEngineDrawReason draw_reason;
} ChessEngineGameStatus;

typedef struct ChessEngineWeightIdentity {
    uint32_t struct_size;
    uint32_t abi_version;
    uint16_t schema_version;
    uint16_t reserved;
    uint64_t identifier;
    uint64_t checksum;
} ChessEngineWeightIdentity;

typedef struct ChessEngineSearchRequest {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t flags;
    uint32_t reserved;
    uint16_t depth;
    uint16_t reserved_depth;
    uint64_t nodes;
    uint64_t soft_time_milliseconds;
    uint64_t hard_time_milliseconds;
    ChessEngineCancellationHandle cancellation_handle;
} ChessEngineSearchRequest;

typedef struct ChessEngineSearchResult {
    uint32_t struct_size;
    uint32_t abi_version;
    ChessEngineBuffer best_move;
    ChessEngineBuffer ponder_move;
    ChessEngineBuffer principal_variation;
    ChessEngineScoreKind score_kind;
    int32_t score_value;
    uint16_t completed_depth;
    uint16_t selective_depth;
    ChessEngineSearchTerminationKind termination_kind;
    ChessEngineSearchFallbackKind fallback_kind;
    uint64_t termination_value;
    uint64_t nodes;
    uint64_t qnodes;
    uint64_t elapsed_milliseconds;
} ChessEngineSearchResult;

uint32_t chess_engine_abi_version(void);

ChessEngineResultCode chess_engine_config_init(ChessEngineConfig *out_config);
ChessEngineResultCode chess_engine_buffer_init(ChessEngineBuffer *out_buffer);
ChessEngineResultCode chess_engine_search_request_init(ChessEngineSearchRequest *out_request);
ChessEngineResultCode chess_engine_search_result_init(ChessEngineSearchResult *out_result);

ChessEngineResultCode chess_engine_last_error_message(ChessEngineBuffer *out_buffer);
ChessEngineResultCode chess_engine_buffer_free(ChessEngineBuffer *buffer);
ChessEngineResultCode chess_engine_search_result_free(ChessEngineSearchResult *result);
ChessEngineResultCode chess_engine_version(ChessEngineBuffer *out_buffer);

ChessEngineResultCode chess_engine_create(
    const ChessEngineConfig *config,
    ChessEngineHandle *out_handle
);
ChessEngineResultCode chess_engine_create_with_indexed_book(
    const ChessEngineConfig *config,
    const uint8_t *book_data,
    size_t book_len,
    uint8_t book_enabled,
    ChessEngineHandle *out_handle
);
ChessEngineResultCode chess_engine_destroy(ChessEngineHandle handle);
ChessEngineResultCode chess_engine_reset_position(ChessEngineHandle handle);
ChessEngineResultCode chess_engine_set_position(
    ChessEngineHandle handle,
    const uint8_t *fen,
    size_t fen_len
);
ChessEngineResultCode chess_engine_get_fen(
    ChessEngineHandle handle,
    ChessEngineBuffer *out_buffer
);
ChessEngineResultCode chess_engine_get_opening_book_move(
    ChessEngineHandle handle,
    ChessEngineBuffer *out_buffer
);
ChessEngineResultCode chess_engine_get_legal_moves(
    ChessEngineHandle handle,
    ChessEngineBuffer *out_buffer
);
ChessEngineResultCode chess_engine_play_move(
    ChessEngineHandle handle,
    const uint8_t *move_text,
    size_t move_len
);
ChessEngineResultCode chess_engine_get_game_status(
    ChessEngineHandle handle,
    ChessEngineGameStatus *out_status
);
ChessEngineResultCode chess_engine_get_weight_identity(
    ChessEngineHandle handle,
    ChessEngineWeightIdentity *out_identity
);

ChessEngineResultCode chess_engine_cancellation_create(
    ChessEngineCancellationHandle *out_handle
);
ChessEngineResultCode chess_engine_cancellation_destroy(
    ChessEngineCancellationHandle handle
);
ChessEngineResultCode chess_engine_cancellation_cancel(
    ChessEngineCancellationHandle handle
);
ChessEngineResultCode chess_engine_cancellation_reset(
    ChessEngineCancellationHandle handle
);
ChessEngineResultCode chess_engine_cancellation_is_cancelled(
    ChessEngineCancellationHandle handle,
    uint8_t *out_cancelled
);

ChessEngineResultCode chess_engine_search(
    ChessEngineHandle handle,
    const ChessEngineSearchRequest *request,
    ChessEngineSearchResult *out_result
);

#ifdef CHESS_ENGINE_ENABLE_TEST_FAULTS
ChessEngineResultCode chess_engine_test_inject_panic(void);
#endif

#ifdef __cplusplus
}
#endif

#endif
