use chess_core::Position;

const PERFT_FIXTURES: &str = include_str!("../../../fixtures/perft.tsv");

#[derive(Clone, Copy, Debug)]
struct PerftFixture<'a> {
    name: &'a str,
    fen: &'a str,
    expected: [u64; 5],
}

fn fixtures() -> Vec<PerftFixture<'static>> {
    PERFT_FIXTURES
        .lines()
        .skip(1)
        .filter(|line| !line.trim().is_empty())
        .map(|line| {
            let fields: Vec<_> = line.split('\t').collect();
            assert_eq!(fields.len(), 7, "invalid perft fixture row: {line}");
            PerftFixture {
                name: fields[0],
                fen: fields[1],
                expected: [
                    fields[2].parse().expect("depth-one count is valid"),
                    fields[3].parse().expect("depth-two count is valid"),
                    fields[4].parse().expect("depth-three count is valid"),
                    fields[5].parse().expect("depth-four count is valid"),
                    fields[6].parse().expect("depth-five count is valid"),
                ],
            }
        })
        .collect()
}

fn assert_fixture_depth(fixture: PerftFixture<'_>, depth: u8) {
    let mut position = Position::from_fen(fixture.fen).expect("authoritative fixture FEN is valid");
    let snapshot = position.clone();
    let expected = fixture.expected[usize::from(depth - 1)];
    let actual = position.perft(depth).expect("authoritative perft succeeds");
    assert_eq!(actual, expected, "{} depth {depth} diverged", fixture.name);
    assert_eq!(
        position, snapshot,
        "{} depth {depth} did not restore the position",
        fixture.name
    );
    position
        .validate_invariants()
        .expect("perft restores every position invariant");
}

#[test]
fn authoritative_perft_fast_depths() {
    for fixture in fixtures() {
        for depth in 1..=3 {
            assert_fixture_depth(fixture, depth);
        }
    }
}

#[test]
#[ignore]
fn authoritative_perft_depth_four() {
    for fixture in fixtures() {
        assert_fixture_depth(fixture, 4);
    }
}

#[test]
#[ignore]
fn authoritative_perft_depth_five() {
    for fixture in fixtures() {
        assert_fixture_depth(fixture, 5);
    }
}
