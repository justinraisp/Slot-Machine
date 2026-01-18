import tkinter as tk
from tkinter import messagebox
import json
import os
from PIL import Image, ImageTk
from main import SlotMachine, load_symbols, load_reel_sets, spin_machine

class SlotMachineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Samba Slot - Interactive Simulator")
        self.root.geometry("675x650")
        self.root.configure(bg="#1a1a1a")
        
        with open("config.json", "r", encoding='utf-8') as f:
            self.config = json.load(f)

        base_cfg = self.config["base"]
        self.rows = base_cfg["window_height"]
        self.cols = 5
        
        symbols_def = load_symbols(base_cfg["symbols"])
        reel_sets = load_reel_sets(base_cfg["reel_sets"], symbols_def)
        self.machine = SlotMachine(reel_sets=reel_sets, window_height=self.rows)
        
        # Slike simbolov
        self.original_images = {}
        self.tk_images = {} 
        if os.path.exists("assets"):
            for filename in os.listdir("assets"):
                if filename.endswith(".png"):
                    name_wo_ext = os.path.splitext(filename)[0]
                    self.original_images[name_wo_ext] = Image.open(f"assets/{filename}")

        # Logika stanja
        self.balance = 1000.0
        self.bet_amount = 1.0
        self.session_total_win = 0.0
        self.last_matrix = None

        # --- UI ELEMENTI ---
        self.label_balance = tk.Label(root, text=f"BALANCE: {self.balance} €", 
                                      font=("Courier", 20, "bold"), bg="#1a1a1a", fg="gold")
        self.label_balance.pack(pady=10)
        self.line_colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
        # OSREDNJI CANVAS (Mreža s kvadratki)
        self.canvas = tk.Canvas(root, bg="#222", highlightthickness=5, highlightbackground="gold")
        self.canvas.pack(pady=10, padx=20, expand=True, fill="both")
        
        self.label_status = tk.Label(root, text="READY TO SPIN", font=("Arial", 12, "bold"), bg="#1a1a1a", fg="white")
        self.label_status.pack()
        
        self.btn_spin = tk.Button(root, text="SPIN", command=self.start_game, 
                                  bg="gold", activebackground="#ffcc00",
                                  font=("Arial", 18, "bold"), width=12, height=1)
        self.btn_spin.pack(pady=20)

        # Ob spremembi velikosti okna ponovno nariši mrežo
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def get_cell_dims(self):
        """Izračuna velikost celic glede na trenutno velikost canvasa."""
        w = self.canvas.winfo_width() // self.cols
        h = self.canvas.winfo_height() // self.rows
        return w, h

    def redraw(self):
        if self.last_matrix:
            self.draw_grid(self.last_matrix)
        else:
            # Začetni izris praznih kvadratkov
            self.draw_grid([["" for _ in range(self.cols)] for _ in range(self.rows)])
            
    def shake_specific_symbols(self, tags_to_shake, count=16, offset=4):
        """Trese samo simbole, ki so dejansko sodelovali pri zmagi."""
        if count <= 0 or not tags_to_shake:
            return

        current_offset = offset if count % 2 == 0 else -offset
        
        for tag in tags_to_shake:
            self.canvas.move(tag, current_offset, 0)
        
        self.root.after(40, lambda: self.shake_specific_symbols(tags_to_shake, count - 1, offset))
    
    def draw_grid(self, matrix, wins=None):
        self.canvas.delete("all")
        self.last_matrix = matrix
        w, h = self.get_cell_dims()

        # 1. Narišemo ločene kvadratke in simbole
        for r in range(self.rows):
            for c in range(self.cols):
                x0, y0 = c * w, r * h
                x1, y1 = x0 + w, y0 + h
                
                # Narišemo kvadratek (Border)
                self.canvas.create_rectangle(x0, y0, x1, y1, outline="#444", width=2)
                
                # Dodamo notranji "inset" efekt za videz ločenih celic
                self.canvas.create_rectangle(x0+4, y0+4, x1-4, y1-4, outline="#333", width=1)

                sym = matrix[r][c]
                mid_x, mid_y = x0 + w//2, y0 + h//2
                
                if sym in self.original_images:
                    # Skaliranje slike, da se prilega kvadratku z nekaj odmika (padding)
                    img = self.original_images[sym].resize((int(w*0.8), int(h*0.8)), Image.LANCZOS)
                    tk_img = ImageTk.PhotoImage(img)
                    self.tk_images[f"{r}_{c}"] = tk_img 
                    symbol_tags = ()
                    if "CP" in sym:
                      symbol_tags = ("CP", f"shake_{r}_{c}")
                    self.canvas.create_image(mid_x, mid_y, image=tk_img, tags=symbol_tags)
                else:
                    self.canvas.create_text(mid_x, mid_y, text=sym, fill="white", font=("Arial", 16, "bold"))

    # 2. Narišemo zmagovalne linije (Winlines)
    def draw_only_lines(self, wins):
        """Nariše samo zmagovalne linije čez obstoječo mrežo."""
        if not wins: 
          return
        for i, win in enumerate(wins):
            if win.get("type") == "line":
                color = self.line_colors[i % len(self.line_colors)]
                self.draw_win_line(win["positions"], color=color)
                
    def draw_win_line(self, positions, color="yellow"):
        w, h = self.get_cell_dims()
        points = []
        for c, r in enumerate(positions):
            points.append(c * w + w//2)
            points.append(r * h + h//2)
        
        self.canvas.create_line(points, fill="white", width=6, capstyle=tk.ROUND)
        self.canvas.create_line(points, fill=color, width=3, capstyle=tk.ROUND)
        
    def show_bonus_trigger_popup(self, num_spins, callback):
        """Prikaže popup ob zadetku bonus igre."""
        popup = tk.Toplevel(self.root)
        popup.title("BONUS TRIGGER!")
        popup.geometry("300x200")
        popup.configure(bg="black")
        popup.transient(self.root)
        popup.grab_set()
        
        # Centriranje popup-a glede na glavno okno
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        popup.geometry(f"+{x}+{y}")

        tk.Label(popup, text=" BONUS ", font=("Arial", 24, "bold"), bg="black", fg="gold").pack(pady=20)
        tk.Label(popup, text=f"Zadeli ste {num_spins} brezplačnih spinov!", font=("Arial", 12), bg="black", fg="white").pack(pady=5)

        def on_click():
            popup.destroy()
            callback()

        btn = tk.Button(popup, text="START FREE SPINS", command=on_click, bg="gold", font=("Arial", 12, "bold"))
        btn.pack(pady=20)
        
    def start_game(self):
        if self.balance < self.bet_amount:
            messagebox.showwarning("Kredit", "Nimate dovolj sredstev!")
            return
        
        self.btn_spin.config(state="disabled", bg="#555")
        self.session_total_win = 0.0
        self.balance -= self.bet_amount
        self.label_balance.config(text=f"BALANCE: {round(self.balance, 2)} €")

        outcome, _ = spin_machine(self.machine, self.config, self.bet_amount, save_log=True)
        self.process_spins(outcome["all_spins"], 0)

    def process_spins(self, all_spins, index):
        if index < len(all_spins):
            current_spin = all_spins[index]
            
            # 1. korak: Narišemo samo simbole (grid)
            self.draw_grid(current_spin["window"])
            
            spin_payout = current_spin["payout"]
            self.session_total_win += spin_payout
            
            # Statusne oznake
            if current_spin["state"] == "base":
                self.label_status.config(text="SPINNING...", fg="white")
            else:
                self.label_status.config(text=f"FREE SPIN {index}!", fg="#00ffff")

            # 2. korak: Z zamikom narišemo linije in preverimo popup
            def show_results():
                # Narišemo linije, če obstajajo
                if "wins" in current_spin:
                    self.draw_only_lines(current_spin["wins"])
                    
                    # Seznam tagov CP simbolov, ki so del zmagovalnih linij
                    winning_cp_tags = []
                    
                    for win in current_spin["wins"]:
                        # Preverimo če je zmagovalni simbol "CP" ali vsebuje "CP"
                        if "CP" in str(win.get("symbols", "")):
                          self.shake_specific_symbols(["CP"])
                    
                    # Stresemo samo tiste, ki so zmagali
                    if winning_cp_tags:
                        self.shake_specific_symbols(winning_cp_tags)
                
                # Če so bili dobitki, posodobimo status
                if spin_payout > 0:
                    self.label_status.config(text=f"WIN: {round(spin_payout, 2)} €", fg="#00ff00")

                # Preverimo za bonus trigger
                if index + 1 < len(all_spins):
                    next_spin = all_spins[index + 1]
                    if current_spin["state"] == "base" and next_spin["state"] == "freespins":
                        self.label_status.config(text="BONUS TRIGGERED!", fg="red")
                        num_free_spins = sum(1 for s in all_spins if s["state"] == "freespins")
                        self.root.after(500, lambda: self.show_bonus_trigger_popup(
                            num_free_spins,
                            lambda: self.process_spins(all_spins, index + 1)
                        ))
                        return 

                # Nadaljujemo na naslednji spin po dodatnem premoru, da igralec vidi linije
                self.root.after(800, lambda: self.process_spins(all_spins, index + 1))

            # Zamik 600ms med ustavitvijo valjev in prikazom linij
            self.root.after(500, show_results)
            
        else:
            self.finalize_session()

    def finalize_session(self):
        self.balance += self.session_total_win
        self.label_balance.config(text=f"BALANCE: {round(self.balance, 2)} €")
        self.btn_spin.config(state="normal", bg="gold")
        
        if self.session_total_win > 0:
            self.label_status.config(text=f"WIN: {round(self.session_total_win, 2)} €!", fg="#00ff00")
        else:
            self.label_status.config(text="READY TO SPIN", fg="white")

if __name__ == "__main__":
    root = tk.Tk()
    app = SlotMachineGUI(root)
    root.mainloop()