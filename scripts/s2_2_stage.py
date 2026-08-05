from pathlib import Path
import base64
import gzip

root = Path(__file__).resolve().parents[1]
parts = [
    (root / f"scripts/.s2_2_payload_{index}").read_text().strip()
    for index in range(4)
]
module = gzip.decompress(base64.b64decode("".join(parts))).decode("utf-8")
module = module.replace(
    "use chess_core::{Color, DrawReason, Game, GameStatus, Position, SearchHistory, UciMove};",
    "use chess_core::{Color, Game, GameStatus, Position, SearchHistory, UciMove};",
)
module = module.replace(
    'let protocol = reader.parse_field("protocol")?;',
    'let protocol: EngineVariantValidationProtocol = reader.parse_field("protocol")?;',
    1,
)
module = module.replace(
    'parse_hex(score_token, "candidate score bits")?',
    'parse_hex(&score_token, "candidate score bits")?',
    1,
)
module_path = root / "crates/chess-tools/src/engine_variant_validation.rs"
module_path.write_text(module)

lib_path = root / "crates/chess-tools/src/lib.rs"
lib = lib_path.read_text()
needle = "pub mod engine_variant;\n"
addition = needle + "pub mod engine_variant_validation;\n"
if addition not in lib:
    if needle not in lib:
        raise SystemExit("engine_variant module declaration not found")
    lib = lib.replace(needle, addition, 1)
lib_path.write_text(lib)
