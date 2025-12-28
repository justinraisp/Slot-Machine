import json
import csv
import statistics
import os
from main import spin_machine, SlotMachine
def run_simulation(total_games, bet_amount):
    with open("config.json", "r", encoding='utf-8') as f:
        config = json.load(f)

    machine = SlotMachine(reel_sets=[], window_height=config["base"]["window_height"])

    results = []
    stats = {
        "total_bet": 0,
        "total_payout": 0,
        "base_payout": 0,
        "bonus_payout": 0
    }

    for i in range(total_games):
        stats["total_bet"] += bet_amount
        outcome, _ = spin_machine(machine, config, bet_amount, save_log=False)
        results.append(outcome["total"])
        stats["total_payout"] += outcome["total"]
        stats["base_payout"] += outcome["base"]
        stats["bonus_payout"] += outcome["bonus"]

    total_rtp = (stats["total_payout"] / stats["total_bet"]) * 100
    base_rtp = (stats["base_payout"] / stats["total_bet"]) * 100
    bonus_rtp = (stats["bonus_payout"] / stats["total_bet"]) * 100

    with open("statistika_iger.csv", mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["Parameter", "Vrednost"])
        writer.writerow(["Skupna stava", stats["total_bet"]])
        writer.writerow(["Skupni RTP (%)", f"{round(total_rtp, 2)}%"])
        writer.writerow(["Base RTP (%)", f"{round(base_rtp, 2)}%"])
        writer.writerow(["Bonus RTP (%)", f"{round(bonus_rtp, 2)}%"])
        writer.writerow(["Base Payout", round(stats["base_payout"], 2)])
        writer.writerow(["Bonus Payout", round(stats["bonus_payout"], 2)])
        writer.writerow(["Standardni odklon", round(statistics.stdev(results), 2)])

    print(f"Simulacija končana. Skupni RTP: {round(total_rtp, 2)}%")

if __name__ == "__main__":
    run_simulation(total_games=1000, bet_amount=1.0)