use chess_core::{Position, SearchHistory};
use chess_search::{
    alpha_beta_search_with_cancellation, AlphaBetaSearchError, SearchCancellationProbe,
    CANCELLATION_CHECK_INTERVAL_NODES,
};

struct BoundaryRequestProbe {
    entered_nodes: u64,
    request_after_nodes: u64,
    requested_at_node: Option<u64>,
    observed_at_node: Option<u64>,
}

impl BoundaryRequestProbe {
    const fn new(request_after_nodes: u64) -> Self {
        Self {
            entered_nodes: 0,
            request_after_nodes,
            requested_at_node: None,
            observed_at_node: None,
        }
    }

    fn observe(&mut self) {
        if self.observed_at_node.is_none() {
            self.observed_at_node = Some(self.entered_nodes);
        }
    }

    fn response_nodes(&self) -> u64 {
        self.observed_at_node
            .expect("request is observed")
            .saturating_sub(self.requested_at_node.expect("request is issued"))
    }
}

impl SearchCancellationProbe for BoundaryRequestProbe {
    fn should_cancel(&mut self) -> bool {
        if self.requested_at_node.is_some() {
            self.observe();
            return true;
        }
        if self.entered_nodes >= self.request_after_nodes {
            self.requested_at_node = Some(self.entered_nodes);
        }
        false
    }

    fn on_node(&mut self) -> bool {
        if self.requested_at_node.is_some() {
            self.observe();
            return true;
        }
        self.entered_nodes = self.entered_nodes.saturating_add(1);
        false
    }
}

#[test]
fn in_tree_request_stops_within_the_node_bound_and_restores_every_root_invariant() {
    let mut position = Position::starting();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut probe = BoundaryRequestProbe::new(64);

    let result = alpha_beta_search_with_cancellation(&mut position, &mut history, 5, &mut probe);

    assert_eq!(result, Err(AlphaBetaSearchError::Cancelled));
    assert!(probe.requested_at_node.is_some());
    assert!(probe.observed_at_node.is_some());
    assert!(
        probe.response_nodes() <= CANCELLATION_CHECK_INTERVAL_NODES,
        "request consumed {} additional nodes with a {}-node bound",
        probe.response_nodes(),
        CANCELLATION_CHECK_INTERVAL_NODES
    );
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
    assert_eq!(history.current_zobrist(), Some(position.zobrist()));
}
