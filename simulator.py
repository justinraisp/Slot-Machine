import json
import csv
import os
import math
import multiprocessing as mp
from datetime import datetime
from main import spin_machine, SlotMachine, load_symbols, load_reel_sets

def worker_task(num_games, bet_amount):
    try:
        with open("config.json", "r", encoding='utf-8') as f:
            config = json.load(f)
        
        base_config = config.get("base")
        if not base_config: return None

        symbols_def = load_symbols(base_config["symbols"])
        reel_sets = load_reel_sets(base_config["reel_sets"], symbols_def)
        machine = SlotMachine(reel_sets=reel_sets, window_height=base_config["window_height"])
        machine.custom_parameters = base_config.get("customParameters", {})

        local_stats = {
            "total_games": num_games,
            "total_payout": 0.0,
            "base_payout": 0.0,
            "bonus_payout": 0.0,
            "bonus_triggers": 0,
            "winning_spins": 0,
            "sum_payout_squares": 0.0,
            "symbol_payouts": {name: 0.0 for name in base_config["symbols"]}
        }

        for _ in range(num_games):
            outcome, _ = spin_machine(machine, config, bet_amount, save_log=False)
            payout = outcome.get("total", 0)
            local_stats["total_payout"] += payout
            local_stats["base_payout"] += outcome.get("base", 0)
            local_stats["bonus_payout"] += outcome.get("bonus", 0)
            
            if payout > 0:
                local_stats["winning_spins"] += 1
            
            multiplier = payout / bet_amount
            local_stats["sum_payout_squares"] += (multiplier ** 2)

            if "wins_by_symbol" in outcome:
                for sym, win_val in outcome["wins_by_symbol"].items():
                    if sym in local_stats["symbol_payouts"]:
                        local_stats["symbol_payouts"][sym] += win_val
            
            if outcome["all_spins"][0]["bonus_triggered"]:
                local_stats["bonus_triggers"] += 1

        return local_stats
    except Exception as e:
        print(f"Napaka v delovnem procesu: {e}")
        return None

def run_simulation(total_games, bet_amount, num_cores=1, existing_filename=None):
    if num_cores > mp.cpu_count() or num_cores < 1:
        num_cores = max(1, mp.cpu_count() - 2)
    games_per_core = max(1, total_games // num_cores)
    
    if not os.path.exists("simulations"):
        os.makedirs("simulations")

    if existing_filename:
        abs_path = os.path.join("simulations", existing_filename)
        rtp_path = abs_path.replace(".json", "_RTP.json")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"simulacija_{timestamp}.json"
        abs_path = os.path.join("simulations", base_name)
        rtp_path = os.path.join("simulations", f"simulacija_{timestamp}_RTP_{total_games}.json")

    if os.path.exists(abs_path):
        print(f"Nadaljujem simulacijo v datoteki: {abs_path}")
        with open(abs_path, "r") as f:
            history = json.load(f)
    else:
        print(f"Ustvarjam novo simulacijo: {abs_path}")
        history = {
            "total_games": 0, "total_bet": 0.0, "total_payout": 0.0,
            "base_payout": 0.0, "bonus_payout": 0.0, "bonus_triggers": 0,
            "winning_spins": 0, "sum_payout_squares": 0.0, "symbol_payouts": {}
        }
    
    print(f"Izvajam {total_games} iger na {num_cores} jedrih...")
    with mp.Pool(processes=num_cores) as pool:
        tasks = [(games_per_core, bet_amount) for _ in range(num_cores)]
        new_results = pool.starmap(worker_task, tasks)

    for res in new_results:
        if not res: continue
        history["total_games"] += res["total_games"]
        history["total_bet"] += (res["total_games"] * bet_amount)
        history["total_payout"] += res["total_payout"]
        history["base_payout"] += res["base_payout"]
        history["bonus_payout"] += res["bonus_payout"]
        history["bonus_triggers"] += res["bonus_triggers"]
        history["winning_spins"] += res["winning_spins"]
        history["sum_payout_squares"] += res["sum_payout_squares"]
        
        for sym, val in res["symbol_payouts"].items():
            history["symbol_payouts"][sym] = history["symbol_payouts"].get(sym, 0.0) + val

    def to_rtp(value):
        return round((value / total_bet), 5)

    n = history["total_games"]
    total_bet = history["total_bet"]
    avg_multiplier = history["total_payout"] / total_bet
    variance = (history["sum_payout_squares"] / n) - (avg_multiplier ** 2)
    std_dev = math.sqrt(max(0, variance))
    # Interval zaupanja za 95% zaupanje
    margin_of_error = 1.96 * (std_dev / math.sqrt(n))
    lower = round((avg_multiplier - margin_of_error), 4)
    upper = round((avg_multiplier + margin_of_error), 4)
    report = {
        "timestamp_last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_games": n,
        "total_bet": total_bet,
        "total_payout_rtp": to_rtp(history['total_payout']),
        "hit_frequency": round((history['winning_spins'] / n), 5),
        "standard_deviation": round(std_dev, 5),
        "bonus_trigger_frequency": round((history['bonus_triggers'] / n), 5),
        "bonus_trigger_hitrate": f"1 in {round(n / max(1, history['bonus_triggers']), 2)}",
        "symbol_payouts_rtp": {sym: to_rtp(val) for sym, val in history["symbol_payouts"].items()},
        "confidence_interval 95%": [lower, upper]
    }

    with open(rtp_path, "w") as f:
        json.dump(report, f, indent=4)

    csv_path = abs_path.replace(".json", ".csv")
    with open(csv_path, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Vrednost"])
        writer.writerow(["Skupni RTP", report["total_payout_rtp"]])
        writer.writerow(["Standardni odklon", report["standard_deviation"]])
        writer.writerow(["Hit Frequency", report["hit_frequency"]])
        writer.writerow(["Bonus Trigger", report["bonus_trigger_hitrate"]])
        writer.writerow([])
        writer.writerow(["Simbol", "RTP %"])
        for sym, val in report["symbol_payouts_rtp"].items():
            writer.writerow([sym, val])

    print(f"\n--- KONČANO ---")
    print(f"Podatki shranjeni v: {abs_path}")
    print(f"Skupni RTP: {report['total_payout_rtp']}")

if __name__ == "__main__":
    # Za novo simulacijo:
    #run_simulation(total_games=5000000, num_cores=6, bet_amount=1.0)
    
    # Za nadaljevanje obstoječe:
    run_simulation(total_games=1000000, bet_amount=1.0, existing_filename="simulacija_20260118_224859_RTP_1000000.json")