import random
from Classes.reelSet import ReelSet
from Classes.payline import Payline
from Classes.paytable import Paytable
from Classes.symbolWindow import SymbolWindow
from Classes.spinWin import SpinWin

class SlotMachine:
    def __init__(self, reel_sets: list[ReelSet], window_height: int):
        self.reelSets: list[ReelSet] = reel_sets
        self.window_height: int = window_height
        self.state: str = "base"
        self.remaining_spins: int = 0
        self.pending_wins: list[SpinWin] = []
        self.custom_parameters: dict = {} 
        self.additional_parameters: dict = {}

    def chooseReelSet(self) -> ReelSet:
        """Izbere set kolutov glede na uteži."""
        return random.choices(
            self.reelSets,
            weights=[rs.weight for rs in self.reelSets],
            k=1
        )[0]

    def getSymbolWindow(self) -> SymbolWindow:
        """
        Generira mrežo simbolov. 
        Tukaj se zgodi le RNG (naključna izbira) pozicij in transformacija simbolov.
        Ne izvajamo nobenih izračunov zmag.
        """
        reel_set = self.chooseReelSet()
        window = SymbolWindow(len(reel_set.reels), self.window_height)
        
        bonus_symbol_base_name = self.custom_parameters.get("bonusSymbol", None)
        cp_weights = self.custom_parameters.get("CPWeights", {})

        for col, reel in enumerate(reel_set.reels):
            stop = random.randint(0, reel.count - 1)
            symbols = reel.get_symbols(stop, self.window_height)

            for row, symbol in enumerate(symbols):
                symbol_copy = symbol.copy()
                if self.state == "freespins" and symbol.name == bonus_symbol_base_name and cp_weights:
                    value = random.choices(list(cp_weights.keys()), weights=list(cp_weights.values()), k=1)[0]
                    symbol_copy.name = f"{bonus_symbol_base_name}_{value}"
                
                window.add_symbol(symbol_copy, row, col)
        
        return window

    def evaluate_symbols(self, symbols: list, paytable: Paytable) -> float:
        """Preveri linijsko zmago za dano zaporedje simbolov."""
        first = symbols[0]
        if first.is_scatter:
            return 0.0
        
        count = 1
        for symbol in symbols[1:]:
            if symbol.name == first.name or symbol.is_wild:
                count += 1
            else:
                break
        
        return paytable.get_payout(first.name, count)

    def evaluate_scatters(self, window: SymbolWindow, paytable: Paytable):
        """Prešteje scatterje in vrne zmage ter morebitne triggerje."""
        scatter_count: dict[str, int] = {}
        for row in window.getMatrix():
            for symbol in row:
                if symbol.is_scatter:
                    scatter_count[symbol.name] = scatter_count.get(symbol.name, 0) + 1

        total_payout = 0.0
        wins: list[SpinWin] = []
        bonus_trigger = None

        for symbol_name, count in scatter_count.items():
            rules = paytable.get_rule(symbol_name, count)
            if not rules:
                continue

            payout = rules.get("payout", 0)
            total_payout += payout
            wins.append(SpinWin(
                type="scatter",
                symbols=[symbol_name] * count,
                payout=payout,
                positions=None, 
                triggers=rules.get("triggers")
            ))

            if "triggers" in rules:
                bonus_trigger = rules["triggers"]

        return total_payout, wins, bonus_trigger

    def _evaluate_collection_feature(self, window: SymbolWindow) -> tuple[float, SpinWin | None]:
        """
        Posebna metoda za preverjanje 'Collection' funkcije (CP simboli).
        Ločena od generiranja okna.
        """
        if self.state != "freespins":
            return 0.0, None

        bonus_symbol_base = self.custom_parameters.get("bonusSymbol", "CP")
        threshold = self.custom_parameters.get("threshold", 0)
        
        current_cp_count = 0
        current_cp_payout = 0
  
        for row in window.getMatrix():
            for symbol in row:
                if symbol.name.startswith(f"{bonus_symbol_base}_"):
                    try:
                        val_str = symbol.name.split("_")[1]
                        val = int(val_str)
                        current_cp_count += 1
                        current_cp_payout += val
                    except (IndexError, ValueError):
                        continue

        if current_cp_count >= threshold and threshold > 0:
            win = SpinWin(
                type="bonus_collection",
                symbols=[bonus_symbol_base] * current_cp_count,
                payout=float(current_cp_payout),
                positions=None,
                triggers="collection_complete"
            )
            return float(current_cp_payout), win
        
        return 0.0, None

    def addTrigger(self, bonus_info: dict, trigger_wins: list[SpinWin] = None):
        """Aktivira bonus igro."""
        self.state = bonus_info.get("name", "freespins")
        self.remaining_spins = bonus_info.get("count", 0)
        if trigger_wins:
            self.pending_wins.extend(trigger_wins)

    def scanMatrix(self, window: SymbolWindow, paylines: list[Payline], paytable: Paytable, bet: float) -> tuple[float, list[SpinWin], dict | None]:
        total_payout = 0.0
        wins: list[SpinWin] = []
        matrix = window.getMatrix()
        num_paylines = len(paylines)

        for payline in paylines:
            symbols = payline.get_symbol_positions(matrix)
            base_payout = self.evaluate_symbols(symbols, paytable)
            
            if base_payout > 0:
                actual_payout = (base_payout * bet) / num_paylines
                total_payout += actual_payout
                wins.append(SpinWin(
                    type="line",
                    symbols=symbols,
                    payout=actual_payout,
                    positions=payline.positions
                ))

        scatter_payout, scatter_wins, bonus_trigger = self.evaluate_scatters(window, paytable)
        actual_scatter_payout = scatter_payout * bet
        total_payout += actual_scatter_payout
        for sw in scatter_wins:
            sw.payout = sw.payout * bet

        if self.state == "freespins":
            bonus_payout, bonus_win = self._evaluate_collection_feature(window)
            if bonus_win:
                actual_bonus_payout = bonus_payout * bet
                total_payout += actual_bonus_payout
                bonus_win.payout = actual_bonus_payout
                wins.append(bonus_win)

        self.pending_wins.extend(wins)
        return total_payout, wins, bonus_trigger