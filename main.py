import uuid
import json
import os
from datetime import datetime
from Classes.symbol import Symbol
from Classes.reel import Reel
from Classes.reelSet import ReelSet
from Classes.payline import Payline
from Classes.paytable import Paytable
from Classes.slotMachine import SlotMachine

def load_symbols(data: dict) -> dict[str, Symbol]:
    symbols = {}
    for name, props in data.items():
        symbols[name] = Symbol(
            name,
            is_wild=props.get("is_wild", False),
            is_scatter=props.get("is_scatter", False)
        )
    return symbols

def load_reel_sets(data: list, symbols: dict[str, Symbol]) -> list[ReelSet]:
    reel_sets = []
    for rs in data:
        reels = []
        for reel_symbols in rs["reels"]:
            reels.append(Reel([symbols[s] for s in reel_symbols]))
        reel_sets.append(ReelSet(reels=reels, weight=rs["weight"]))
    return reel_sets

def load_paylines(data: list) -> list[Payline]:
    return [Payline(p) for p in data]

def load_paytable(data: dict) -> Paytable:
    paytable = Paytable()
    for symbol, rules in data.items():
        for count_str, rule_info in rules.items():
            count = int(count_str)
            if isinstance(rule_info, (int, float)):
                paytable.add_rule(symbol, count, {"payout": rule_info})
            elif isinstance(rule_info, dict):
                paytable.add_rule(symbol, count, rule_info)
    return paytable

def spin_machine(machine: SlotMachine, config: dict, bet: float, save_log: bool = True):
    session_id = str(uuid.uuid4())
    session_data = {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "bet": bet,
        "base_win": 0.0,
        "bonus_win": 0.0,
        "total_payout": 0.0,
        "spins": [],
        "wins_by_symbol": {name: 0.0 for name in config["base"]["symbols"]},
        "total_freespins_played": 0
    }

    first_window_matrix = None

    def update_machine_config(state):
        used_config = config[state]
        symbols = load_symbols(used_config["symbols"])
        reel_sets = load_reel_sets(used_config["reel_sets"], symbols)
        paylines = load_paylines(used_config["paylines"])
        paytable = load_paytable(used_config["paytable"])
        
        machine.reelSets = reel_sets
        machine.paylines = paylines
        machine.paytable = paytable
        machine.state = state
        machine.custom_parameters = used_config.get("customParameters", {})

    update_machine_config("base")

    def single_spin():
        nonlocal first_window_matrix 
        
        window = machine.getSymbolWindow()
        
        if first_window_matrix is None:
            first_window_matrix = window.getMatrix()

        spin_state = machine.state
        total, wins, bonus_trigger = machine.scanMatrix(window, machine.paylines, machine.paytable, bet)
        
        if spin_state == "base":
            session_data["base_win"] += total
        else:
            session_data["bonus_win"] += total
            session_data["total_freespins_played"] += 1
        
        session_data["total_payout"] += total

        for w in wins:
            if w.symbols and len(w.symbols) > 0:
                s = w.symbols[0]
                sym_name = s.name if hasattr(s, 'name') else str(s)
                if sym_name in session_data["wins_by_symbol"]:
                    session_data["wins_by_symbol"][sym_name] += w.payout

        spin_log = {
            "state": spin_state,
            "window": [[s.name for s in row] for row in window.getMatrix()],
            "payout": round(total, 2),
            "wins": [
                {
                    "type": w.type,
                    "symbols": [s.name if hasattr(s, 'name') else s for s in w.symbols],
                    "payout": round(w.payout, 2),
                    "positions": w.positions,
                    "triggers": w.triggers
                } for w in wins
            ],
            "bonus_triggered": {
                "name": bonus_trigger["name"],
                "spins_awarded": bonus_trigger["count"]
            } if bonus_trigger else None
        }
        
        session_data["spins"].append(spin_log)

        if bonus_trigger and spin_state == "base":
            update_machine_config("freespins")
            machine.remaining_spins = bonus_trigger['count']

        if spin_state == "freespins":
            machine.remaining_spins -= 1
            if machine.remaining_spins <= 0:
                machine.state = "base"

    single_spin() 
    while machine.state == "freespins" and machine.remaining_spins > 0:
        single_spin()

    session_data["total_payout"] = round(session_data["total_payout"], 4)
    session_data["base_win"] = round(session_data["base_win"], 4)
    session_data["bonus_win"] = round(session_data["bonus_win"], 4)

    if save_log:
        save_session_to_json(session_data)
    
    return {
        "total": session_data["total_payout"],
        "base": session_data["base_win"],
        "bonus": session_data["bonus_win"],
        "all_spins": session_data["spins"],
        "wins_by_symbol": session_data["wins_by_symbol"]
    }, session_id
  
def save_session_to_json(data):
    if not os.path.exists('database'):
        os.makedirs('database')
        
    filename = f"database/log_{data['session_id'][:8]}.json"
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\nSeja shranjena v {filename}")
    
def main():
    try:
        with open("config.json", "r", encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Napaka: Datoteka config.json ni bila najdena.")
        return

    BET_AMOUNT = 1.0
    machine = SlotMachine(reel_sets=[], window_height=config["base"]["window_height"])
    
    outcome, session_id = spin_machine(machine, config, BET_AMOUNT, save_log=True)
    print(f"\n--- KONČNI REZULTAT SEJE ---")
    print(f"ID: {session_id}")
    print(f"Vložek: {BET_AMOUNT}")
    print(f"Dobitek v osnovni igri: {outcome['base']}")
    print(f"Dobitek v bonusih: {outcome['bonus']}")
    print(f"Skupno izplačilo: {outcome['total']}")
    print(f"Neto rezultat: {round(outcome['total'] - BET_AMOUNT, 2)}")

if __name__ == "__main__":
    main()