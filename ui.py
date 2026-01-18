import tkinter as tk
from tkinter import messagebox
import json
import os
from PIL import Image, ImageTk
from main import SlotMachine, load_symbols, load_reel_sets, spin_machine

class SlotMachineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Samba Slot - Bonus Tracker")
        self.root.geometry("600x650")
        
        with open("config.json", "r", encoding='utf-8') as f:
            self.config = json.load(f)

        base_cfg = self.config["base"]
        symbols_def = load_symbols(base_cfg["symbols"])
        reel_sets = load_reel_sets(base_cfg["reel_sets"], symbols_def)
        
        self.machine = SlotMachine(reel_sets=reel_sets, window_height=base_cfg["window_height"])
        
        self.original_images = {}
        self.current_tk_images = {} 
        
        for sym_name in base_cfg["symbols"].keys():
            img_path = f"assets/{sym_name}.png"
            if os.path.exists(img_path):
                self.original_images[sym_name] = Image.open(img_path)

        self.balance = 1000.0
        self.bet_amount = 1.0
        self.session_total_win = 0.0
        self.last_matrix = None

        self.label_balance = tk.Label(root, text=f"Kredit: {self.balance} €", font=("Arial", 16, "bold"))
        self.label_balance.pack(pady=10)
        
        self.label_status = tk.Label(root, text="Pritisni SPIN za začetek", font=("Arial", 12, "italic"), fg="gray")
        self.label_status.pack()

        self.reels_frame = tk.Frame(root, bg="#222", padx=10, pady=10)
        self.reels_frame.pack(pady=10, expand=True, fill="both")
        
        self.grid_labels = []
        for r in range(base_cfg["window_height"]):
            self.reels_frame.grid_rowconfigure(r, weight=1)
            row_labels = []
            for c in range(5):
                self.reels_frame.grid_columnconfigure(c, weight=1)
                
                cell_container = tk.Frame(self.reels_frame, bg="#222")
                cell_container.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
                
                lbl = tk.Label(cell_container, text="?", bg="#444", fg="white", 
                               font=("Arial", 14, "bold"), compound="center")
                lbl.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0)
                
                row_labels.append(lbl)
            self.grid_labels.append(row_labels)

        self.reels_frame.bind("<Configure>", self.on_resize)

        self.label_spin_win = tk.Label(root, text="Dobitek spina: 0.00 €", font=("Arial", 12), fg="green")
        self.label_spin_win.pack()
        
        self.label_total_session_win = tk.Label(root, text="", font=("Arial", 20, "bold"), fg="gold", bg="black")
        self.label_total_session_win.pack(pady=10, fill="x")
        
        self.btn_spin = tk.Button(root, text="SPIN!", command=self.start_game, bg="gold",
                                  font=("Arial", 14, "bold"), width=15, height=2)
        self.btn_spin.pack(pady=20)

    def on_resize(self, event):
        """Metoda, ki se sproži ob vsaki spremembi velikosti mreže."""
        if self.last_matrix:
            self.update_grid(self.last_matrix)

    def update_grid(self, matrix_names):
        self.last_matrix = matrix_names
        try:
            sample_cell = self.grid_labels[0][0]
            target_w = sample_cell.winfo_width()
            target_h = sample_cell.winfo_height()
            
            if target_w < 10: target_w, target_h = 100, 100
        except:
            target_w, target_h = 100, 100

        for r in range(len(matrix_names)):
            for c in range(len(matrix_names[r])):
                sym = matrix_names[r][c]
                lbl = self.grid_labels[r][c]
                
                if sym in self.original_images:
                    orig_img = self.original_images[sym]
                    resized_img = orig_img.resize((target_w - 10, target_h - 10), Image.LANCZOS)
                    tk_img = ImageTk.PhotoImage(resized_img)
                    
                    self.current_tk_images[f"{r}_{c}"] = tk_img
                    lbl.config(image=tk_img, text="")
                else:
                    color = "white"
                    lbl.config(image="", text=sym, fg=color)

    def start_game(self):
        if self.balance < self.bet_amount:
            messagebox.showwarning("Stanje", "Nimate dovolj kredita!")
            return
        
        self.session_total_win = 0.0
        self.label_total_session_win.config(text="", bg="SystemButtonFace")
        self.btn_spin.config(state="disabled")
        self.balance -= self.bet_amount
        self.label_balance.config(text=f"Kredit: {round(self.balance, 2)} €")

        outcome, _ = spin_machine(self.machine, self.config, self.bet_amount, save_log=True)
        self.process_spins(outcome["all_spins"], 0)

    def process_spins(self, all_spins, index):
        if index < len(all_spins):
            current_spin = all_spins[index]
            self.update_grid(current_spin["window"])
            
            spin_payout = current_spin["payout"]
            self.session_total_win += spin_payout
            
            if current_spin["state"] == "base":
                self.label_status.config(text="OSNOVNA IGRA", fg="blue")
            else:
                self.label_status.config(text=f"FREE SPIN: {index} / {len(all_spins)-1}", fg="red")
            
            self.label_spin_win.config(text=f"Dobitek spina: {round(spin_payout, 2)} €")
            
            if self.session_total_win > 0:
                self.label_total_session_win.config(text=f"TRENUTNI DOBITEK: {round(self.session_total_win, 2)} €", bg="black")

            self.root.after(1000, lambda: self.process_spins(all_spins, index + 1))
        else:
            self.finalize_session()

    def finalize_session(self):
        self.balance += self.session_total_win
        self.label_balance.config(text=f"Kredit: {round(self.balance, 2)} €")
        
        if self.session_total_win > 0:
            self.label_total_session_win.config(text=f"TOTAL WIN: {round(self.session_total_win, 2)} €", bg="#CCAC00", fg="black")
            self.label_status.config(text="ČESTITAMO!", fg="green")
        else:
            self.label_status.config(text="Več sreče prihodnjič", fg="gray")
            self.label_total_session_win.config(text="BREZ DOBITKA", bg="gray", fg="white")
        self.btn_spin.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = SlotMachineGUI(root)
    root.mainloop()