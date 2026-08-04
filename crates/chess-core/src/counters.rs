use core::fmt;

/// Number of reversible halfmoves since the last pawn move or capture.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct HalfmoveClock(u16);

impl HalfmoveClock {
    /// Creates a halfmove clock from its stored value.
    #[must_use]
    pub const fn new(value: u16) -> Self {
        Self(value)
    }

    /// Returns the stored number of halfmoves.
    #[must_use]
    pub const fn get(self) -> u16 {
        self.0
    }

    /// Resets the clock after a pawn move or capture.
    pub fn reset(&mut self) {
        self.0 = 0;
    }

    /// Increments the clock, returning `None` on overflow.
    pub fn checked_increment(&mut self) -> Option<()> {
        self.0 = self.0.checked_add(1)?;
        Some(())
    }
}

impl fmt::Display for HalfmoveClock {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

/// One-based fullmove number from FEN and game notation.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct FullmoveNumber(u16);

impl FullmoveNumber {
    /// Standard starting fullmove number.
    pub const ONE: Self = Self(1);

    /// Creates a fullmove number, rejecting zero.
    #[must_use]
    pub const fn new(value: u16) -> Option<Self> {
        if value == 0 {
            None
        } else {
            Some(Self(value))
        }
    }

    /// Returns the stored one-based number.
    #[must_use]
    pub const fn get(self) -> u16 {
        self.0
    }

    /// Increments after Black moves, returning `None` on overflow.
    pub fn checked_increment(&mut self) -> Option<()> {
        self.0 = self.0.checked_add(1)?;
        Some(())
    }
}

impl Default for FullmoveNumber {
    fn default() -> Self {
        Self::ONE
    }
}

impl fmt::Display for FullmoveNumber {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

#[cfg(test)]
mod tests {
    use core::mem::size_of;

    use super::{FullmoveNumber, HalfmoveClock};

    #[test]
    fn halfmove_clock_is_typed_and_checked() {
        let mut clock = HalfmoveClock::new(99);
        assert_eq!(clock.get(), 99);
        assert_eq!(clock.checked_increment(), Some(()));
        assert_eq!(clock.get(), 100);
        clock.reset();
        assert_eq!(clock, HalfmoveClock::default());
        assert_eq!(clock.to_string(), "0");

        let mut maximum = HalfmoveClock::new(u16::MAX);
        assert_eq!(maximum.checked_increment(), None);
        assert_eq!(maximum.get(), u16::MAX);
        assert_eq!(size_of::<HalfmoveClock>(), 2);
    }

    #[test]
    fn fullmove_number_is_one_based_and_checked() {
        assert_eq!(FullmoveNumber::new(0), None);
        let mut number = FullmoveNumber::new(1).expect("one is valid");
        assert_eq!(number, FullmoveNumber::default());
        assert_eq!(number.checked_increment(), Some(()));
        assert_eq!(number.get(), 2);
        assert_eq!(number.to_string(), "2");

        let mut maximum = FullmoveNumber::new(u16::MAX).expect("maximum is nonzero");
        assert_eq!(maximum.checked_increment(), None);
        assert_eq!(maximum.get(), u16::MAX);
        assert_eq!(size_of::<FullmoveNumber>(), 2);
    }
}
