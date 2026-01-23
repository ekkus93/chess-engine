# Move representation and parsing

class Move:
    def __init__(self, start, end, promotion=None):
        self.start = start
        self.end = end
        self.promotion = promotion

    def __repr__(self):
        return f"Move({self.start}->{self.end}, promo={self.promotion})"
