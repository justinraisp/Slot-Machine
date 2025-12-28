class SpinWin:
    def __init__(self, type: str, symbols: list, payout: float, positions: list = None, triggers: str = None):
        self.type = type  # npr. "line", "scatter", "bonus"
        self.symbols = symbols  # seznam simbolov, ki so ustvarili dobitno kombinacijo
        self.payout = payout  # izplačilo za to dobitno kombinacijo
        self.positions = positions  # položaji simbolov na zaslonu (če je primerno)
        self.triggers = triggers  # dodatne informacije o sprožilcih (če je primerno)