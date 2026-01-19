import tkinter as tk
from tkinter import messagebox
import json
import os
import random
import customtkinter as ctk
from PIL import Image, ImageTk
from main import SlotMachine, load_symbols, load_reel_sets, spin_machine

class SlotMachineGUI:
  def __init__(self, root):
    self.root = root
    self.root.title("Slot machine simulator")
    self.root.geometry("1000x750")
    self.root.minsize(525, 500)
    self.root.configure(bg="#474646")
    
    with open("config.json", "r", encoding='utf-8') as f:
      self.config = json.load(f)
    with open("rules.txt", "r", encoding="utf-8") as f:
      rules_text = f.read()

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
    self.balance = 500.0
    self.bet_amount = 1.0
    self.session_total_win = 0.0
    self.last_matrix = None

    # UI ELEMENTI
    # SPODNJA NADZORNA PLOŠČA (Control Bar)
    self.controls_frame = tk.Frame(root, bg="#1a1a1a", height=100)
    self.controls_frame.pack(side=tk.BOTTOM, fill="x", pady=20, padx=20)
    
    self.left_info_frame = tk.Frame(self.controls_frame, bg="#1a1a1a")
    self.left_info_frame.pack(side=tk.LEFT, padx=15)
    
    self.label_balance = tk.Label(self.left_info_frame, text=f"Credit: {self.balance:.2f} €", 
                    font=("Arial", 10, "bold"), bg="#1a1a1a", fg="gold")
    self.label_balance.pack(side=tk.TOP, anchor="w", pady=(0, 5))
    self.line_colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
    # OSREDNJI CANVAS (Mreža s kvadratki)
    self.canvas = tk.Canvas(root, bg="#222", highlightthickness=5, highlightbackground="gold")
    self.canvas.pack(pady=10, padx=20, expand=True, fill="both")
    
    self.label_status = tk.Label(root, text="Ready to spin", font=("Arial", 12, "bold"), bg="#1a1a1a", fg="gold")
    self.label_status.pack()
    
    self.btn_info = tk.Button(
      self.controls_frame,
      text="Info",
      command=lambda:self.show_info_page(rules_text=rules_text),
      bg="#333",
      fg="white",
      font=("Arial", 12, "bold"),
      width=6
    )
    self.btn_info.pack(side=tk.RIGHT, padx=10)

    # Okvir za kontrole stave (Bet Controls)
    self.bet_frame = tk.Frame(self.left_info_frame, bg="#1a1a1a")
    self.bet_frame.pack(side=tk.TOP, anchor="w")

    tk.Label(self.bet_frame, text="Bet: ", font=("Arial", 10, "bold"), 
         bg="#1a1a1a", fg="gold").pack(side=tk.LEFT)

    # Nastavitve stave
    self.bet_options = [0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
    # Poiščemo index trenutne stave (privzeto 1.0 € je na indexu 2)
    self.current_bet_index = self.bet_options.index(self.bet_amount)

    # Gumb MINUS
    self.btn_minus = tk.Button(self.bet_frame, text="-", command=self.decrease_bet,
                   bg="#333", fg="white", font=("Arial", 12, "bold"), 
                   width=3, relief="flat")
    self.btn_minus.pack(side=tk.LEFT, padx=2)

    # Labela za prikaz trenutne stave
    self.label_bet_display = tk.Label(self.bet_frame, text=f"{self.bet_amount:.2f} €", 
                      font=("Arial", 12, "bold"), bg="#1a1a1a", fg="gold", width=5)
    self.label_bet_display.pack(side=tk.LEFT, padx=2)

    # Gumb PLUS
    self.btn_plus = tk.Button(self.bet_frame, text="+", command=self.increase_bet,
                  bg="#333", fg="white", font=("Arial", 12, "bold"), 
                  width=3, relief="flat")
    self.btn_plus.pack(side=tk.LEFT, padx=2)
    
    self.btn_spin = tk.Button(self.controls_frame, text="Spin", command=self.start_game, 
                  bg="gold", activebackground="#ffcc00",
                  font=("Arial", 16, "bold"), width=8, height=1)
    self.btn_spin.pack(side=tk.RIGHT, padx=20)
    self.canvas.bind("<Configure>", lambda e: self.redraw())
    
  def show_info_page(self, rules_text):
    info = tk.Toplevel(self.root)
    info.title("Paytable & Rules")
    info.geometry("800x850") # Malce širše
    info.configure(bg="#0a0a0a")
    info.transient(self.root)
    info.grab_set()

    # 1. DODAMO GLAVNI CANVAS IN SCROLLBAR, DA VIDIMO VSE
    main_canvas = tk.Canvas(info, bg="#0a0a0a", highlightthickness=0)
    v_scroll = tk.Scrollbar(info, orient="vertical", command=main_canvas.yview)
    # Okvir znotraj canvsa, v katerega bomo dajali vse elemente
    scrollable_frame = tk.Frame(main_canvas, bg="#0a0a0a")

    scrollable_frame.bind(
      "<Configure>",
      lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
    )

    main_canvas.create_window((400, 0), window=scrollable_frame, anchor="n")
    main_canvas.configure(yscrollcommand=v_scroll.set)

    v_scroll.pack(side="right", fill="y")
    main_canvas.pack(side="left", expand=True, fill="both")

    # CENTER OKNA
    x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 400
    y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 425
    info.geometry(f"+{x}+{y}")
    
    # GAME RULES
    tk.Label(scrollable_frame, text="Game rules", font=("Impact", 24, "bold"), bg="#0a0a0a", fg="gold").pack(pady=(30, 5))
    
    rules_txt_box = tk.Text(scrollable_frame, wrap="word", bg="#121212", fg="#ccc", 
                font=("Arial", 10), relief="flat", height=20, width=85, padx=20, pady=20)
    rules_txt_box.pack(padx=40, pady=10)

    rules_txt_box.tag_configure("header", font=("Arial", 12, "bold"), foreground="gold")
    rules_txt_box.tag_configure("subheader", font=("Arial", 10, "bold"), foreground="#ff6600")
    rules_txt_box.tag_configure("bullet", font=("Arial", 10, "bold"), foreground="#00ccff")
    rules_txt_box.tag_configure("body", font=("Arial", 10), foreground="#bbbbbb")

    rules_txt_box.config(state="normal")
    
    # Logika za avtomatsko stiliziranje tvojega .txt besedila
    for line in rules_text.split('\n'):
      stripped = line.strip()
      
      if not stripped: # Prazna vrstica
        rules_txt_box.insert(tk.END, "\n")
      elif stripped.isupper() and "=" not in stripped: # Glavni naslovi (vse velike črke)
        rules_txt_box.insert(tk.END, line + "\n", "header")
      elif "---" in line or "===" in line: # Ločilne črte v txt
        rules_txt_box.insert(tk.END, line + "\n", "subheader")
      elif stripped.startswith("-"):
        rules_txt_box.insert(tk.END, "  " + stripped[:1], "bullet")
        rules_txt_box.insert(tk.END, stripped[1:] + "\n", "body")
      else: # Navadno besedilo
        rules_txt_box.insert(tk.END, line + "\n", "body")

    rules_txt_box.config(state="disabled")
    
    # NASLOV
    tk.Label(scrollable_frame, text="Paytable", font=("Arial", 20, "bold"), bg="#0a0a0a", fg="#ff6600").pack(pady=(20, 0))
    tk.Label(scrollable_frame, text=f"Values based on current bet: {self.bet_amount:.2f} €", 
         font=("Arial", 10, "bold"), bg="#0a0a0a", fg="gold").pack(pady=(0, 20))
    # MREŽA SIMBOLOV
    pay_frame = tk.Frame(scrollable_frame, bg="#0a0a0a")
    pay_frame.pack(fill="x", padx=30)
    for c in range(4):
      pay_frame.grid_columnconfigure(c, weight=1)

    multiplier = 20
    pay_data = [
      {"sym": "P1", "wins": [("5", 1000/multiplier), ("4", 200/multiplier), ("3", 50/multiplier)]},
      {"sym": "P2", "wins": [("5", 500/multiplier), ("4", 100/multiplier), ("3", 20/multiplier)]},
      {"sym": "P3", "wins": [("5", 250/multiplier), ("4", 50/multiplier), ("3", 10/multiplier)]},
      {"sym": "SCAT", "special": "5 free spins", "wins": [("3", 0)]},
      {"sym": "P4", "wins": [("5", 100/multiplier), ("4", 25/multiplier), ("3", 5/multiplier)]},
      {"sym": "P5", "wins": [("5", 100/multiplier), ("4", 25/multiplier), ("3", 5/multiplier)]},
      {"sym": "P6", "wins": [("5", 100/multiplier), ("4", 25/multiplier), ("3", 5/multiplier)]},
    ]

    self.pay_imgs = []
    for i, item in enumerate(pay_data):
      col, row = i % 4, i // 4
      card = tk.Frame(pay_frame, bg="#0a0a0a", padx=10, pady=15)
      card.grid(row=row, column=col, sticky="nsew")

      sym_name = item["sym"]
      if sym_name in self.original_images:
        img = self.original_images[sym_name].resize((70, 70), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        self.pay_imgs.append(tk_img)
        tk.Label(card, image=tk_img, bg="#0a0a0a", highlightthickness=1, highlightbackground="gold").pack()
      else:
        tk.Label(card, text=sym_name, fg="white", bg="#333", width=8, height=4).pack()

      wins_frame = tk.Frame(card, bg="#0a0a0a")
      wins_frame.pack(pady=5)

      if "special" in item:
        tk.Label(wins_frame, text=item["special"], font=("Arial", 9, "bold"), fg="#00ffff", bg="#0a0a0a").pack()
        tk.Label(wins_frame, text=f"{item['wins'][0][0]}x to trigger", font=("Arial", 8), fg="white", bg="#0a0a0a").pack()
      else:
        for count, mult in item["wins"]:
          actual_win = mult * self.bet_amount
          row_f = tk.Frame(wins_frame, bg="#0a0a0a")
          row_f.pack(anchor="center")
          tk.Label(row_f, text=f"{count}x", font=("Arial", 9, "bold"), bg="#0a0a0a", fg="#00ccff").pack(side="left")
          tk.Label(row_f, text=f" {actual_win:.2f}€", font=("Arial", 9, "bold"), bg="#0a0a0a", fg="white").pack(side="left")

    # PAYLINES
    tk.Label(scrollable_frame, text="PAYLINES", font=("Arial", 14, "bold"), bg="#0a0a0a", fg="gold").pack(pady=(20, 5))
    line_grid_frame = tk.Frame(scrollable_frame, bg="#0a0a0a")
    line_grid_frame.pack(pady=10)

    # Tukaj preberemo tvoje linije
    paylines_data = [[1, 1, 1, 1, 1], [0, 0, 0, 0, 0], [2, 2, 2, 2, 2], [0, 1, 2, 1, 0], [2, 1, 0, 1, 2], [0, 0, 1, 0, 0], [2, 2, 1, 2, 2], [1, 2, 2, 2, 1], [1, 0, 0, 0, 1], [0, 1, 1, 1, 0], [2, 1, 1, 1, 2], [0, 1, 0, 1, 0], [2, 1, 2, 1, 2], [1, 0, 1, 0, 1], [1, 2, 1, 2, 1], [1, 1, 0, 1, 1], [1, 1, 2, 1, 1], [0, 2, 0, 2, 0], [2, 0, 2, 0, 2], [1, 0, 2, 0, 1]]

    for i, line in enumerate(paylines_data):
      # i*2 ker moramo rezervirati eno vrstico za številko
      col, row = i % 5, (i // 5) * 2 
      
      line_canvas = tk.Canvas(line_grid_frame, width=80, height=50, bg="#1a1a1a", highlightthickness=1, highlightbackground="#444")
      line_canvas.grid(row=row, column=col, padx=5, pady=(5, 0))
      
      cell_w, cell_h = 80 // 5, 50 // 3
      for r_idx in range(3):
        for c_idx in range(5):
          fill_color = "#ff6600" if line[c_idx] == r_idx else "#333"
          line_canvas.create_rectangle(c_idx*cell_w+1, r_idx*cell_h+1, (c_idx+1)*cell_w-1, (r_idx+1)*cell_h-1, fill=fill_color, outline="")

      # Številka linije v vrstico TAKOJ pod kanvasom
      tk.Label(line_grid_frame, text=f"L{i+1}", font=("Arial", 7), bg="#0a0a0a", fg="white").grid(row=row+1, column=col, pady=(0, 5))

    tk.Button(scrollable_frame, text="CLOSE", command=info.destroy, bg="gold", font=("Arial", 12, "bold"), width=15).pack(pady=30)

  def update_bet_display(self):
    """Posodobi vrednost stave in tekst na zaslonu."""
    self.bet_amount = self.bet_options[self.current_bet_index]
    self.label_bet_display.config(text=f"{self.bet_amount:.2f} €")
    # Pokličemo še tvojo obstoječo funkcijo za status
    self.label_status.config(text=f"BET CHANGED TO {self.bet_amount} €", fg="gold")

  def increase_bet(self):
    """Poveča stavo za eno stopnjo."""
    if self.current_bet_index < len(self.bet_options) - 1:
      self.current_bet_index += 1
      self.update_bet_display()

  def decrease_bet(self):
    """Zmanjša stavo za eno stopnjo."""
    if self.current_bet_index > 0:
      self.current_bet_index -= 1
      self.update_bet_display()
      
  def process_spins(self, all_spins, index):
    if index < len(all_spins):
      current_spin = all_spins[index]
      
      # 1. korak: Narišemo samo simbole (grid)
      self.draw_grid(current_spin["window"])
      
      spin_payout = current_spin["payout"]
      self.session_total_win += spin_payout
      
      # Statusne oznake
      if current_spin["state"] == "base":
        pass
      else:
        self.label_status.config(text=f"FREE SPIN {index}!", fg="#00ffff")

      # 2. korak: Z zamikom narišemo linije in preverimo popup
      def show_results():
        # Narišemo linije, če obstajajo
        shake = False
        if "wins" in current_spin:
          self.draw_only_lines(current_spin["wins"])
          
          for win in current_spin["wins"]:
            # Preverimo če je zmagovalni simbol "CP" ali vsebuje "CP"
            symbols_list = win.get("symbols", [])
            if symbols_list and all(s == "CP" for s in symbols_list):
              self.shake_specific_symbols(["CP"])
              shake = True
                  
        # Če so bili dobitki, posodobimo status
        if spin_payout > 0:
          self.label_status.config(text=f"WIN: {round(spin_payout, 2)} €", fg="#00ff00")
        
        # Preverimo za bonus trigger
        if index + 1 < len(all_spins):
          next_spin = all_spins[index + 1]
          if current_spin["state"] == "base" and next_spin["state"] == "freespins":
            self.label_status.config(text="BONUS TRIGGERED!", fg="red")
            num_free_spins = sum(1 for s in all_spins if s["state"] == "freespins")
            self.root.after(2000, lambda: self.show_bonus_trigger_popup(
              num_free_spins,
              lambda: self.animate_spin(all_spins, step=0, index = index + 1)
            ))
            return 
          if shake:
            self.root.after(2000, lambda: self.animate_spin(all_spins, step=0, index=index + 1))
          else: 
            self.root.after(1000, lambda: self.animate_spin(all_spins, step=0, index=index + 1))
        else:
          self.root.after(1000, lambda: self.process_spins(all_spins, index + 1))

      if current_spin["state"] == "base":
        self.root.after(400, show_results)
      else:
        self.root.after(1000, show_results)
      
    else:
      self.finalize_session()
        
  def animate_spin(self, final_all_spins, step=0, index=0):
    """Ustvari učinek vrtenja z naključnimi simboli."""
    if step < 15:  # Število premikov pred ustavitvijo      
      # Ustvarimo matriko z naključnimi simboli iz naloženih slik
      random_matrix = []
      if final_all_spins and index < len(final_all_spins):
        current_state = final_all_spins[index].get("state", "base")
      if current_state == "base":
        raw_symbols = list(self.original_images.keys()) if self.original_images else ["?"]
        if "BLANK" in raw_symbols:
          raw_symbols.remove("BLANK")
        weighted_symbols = []
        for s in raw_symbols:
          if s.startswith("CP"):
            weighted_symbols.append(s)
          else:
            for _ in range(4):
              weighted_symbols.append(s)
      else: 
        raw_symbols = list(self.original_images.keys()) if self.original_images else ["?"]
        weighted_symbols = []
        for s in raw_symbols:
          if s.startswith("P") or s == "WILD" or s == "SCAT":
            pass
          elif s.startswith("CP"):
            weighted_symbols.append(s)
          else:
            for _ in range(10):
              weighted_symbols.append(s)
      for r in range(self.rows):
        row = [random.choice(weighted_symbols) for _ in range(self.cols)]
        random_matrix.append(row)
      
      self.draw_grid(random_matrix)
      # Hitrost vrtenja: 60ms med menjavo simbolov
      self.root.after(50, lambda: self.animate_spin(final_all_spins, step + 1, index))
    else:
      # Ko je animacija končana, pokažemo dejanski rezultat
      self.process_spins(final_all_spins, index)

  def get_cell_dims(self):
    """Izračuna velikost celic glede na trenutno velikost canvasa."""
    w = self.canvas.winfo_width() // self.cols
    h = self.canvas.winfo_height() // self.rows
    return w, h

  def get_dynamic_font_size(self, base_size):
    """Izračuna velikost pisave glede na trenutno širino okna."""
    # 675 je tvoja začetna širina okna (geometry)
    current_width = self.root.winfo_width()
    scale = current_width / 675
    return int(base_size * scale)

  def redraw(self):
    # Izračunamo nove velikosti
    size_balance = self.get_dynamic_font_size(12)
    size_spin = self.get_dynamic_font_size(18)
    size_status = self.get_dynamic_font_size(12)
    size_bet = self.get_dynamic_font_size(12)

    # Posodobimo pisave elementov
    self.label_balance.config(font=("Arial", size_balance, "bold"))
    self.btn_spin.config(font=("Arial", size_spin, "bold"))
    self.label_status.config(font=("Arial", size_status, "bold"))
    self.label_bet_display.config(font=("Arial", size_bet, "bold"))
    
    # Posodobimo pisavo napisa "BET:" znotraj bet_frame-a
    # Najdemo labelo v okvirju (prvi otrok)
    for child in self.bet_frame.winfo_children():
      if isinstance(child, tk.Label):
        child.config(font=("Arial", size_bet, "bold"))
        
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
          text_font_size = self.get_dynamic_font_size(16)
          self.canvas.create_text(mid_x, mid_y, text=sym, fill="white", 
                font=("Arial", text_font_size, "bold"))

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
    tk.Label(popup, text=f"You won {num_spins} free spins!", font=("Arial", 12), bg="black", fg="white").pack(pady=5)

    def on_click():
      popup.destroy()
      callback()

    btn = tk.Button(popup, text="Start freespins", command=on_click, bg="gold", font=("Arial", 12, "bold"))
    btn.pack(pady=20)
    
  def start_game(self):
    if self.balance < self.bet_amount:
      messagebox.showwarning("Credit", "Not enough credit!")
      return
    
    self.btn_spin.config(state="disabled", bg="#555")
    self.btn_plus.config(state="disabled")
    self.btn_minus.config(state="disabled")
    self.session_total_win = 0.0
    self.balance -= self.bet_amount
    self.label_balance.config(text=f"Credit: {self.balance:.2f} €")
    self.label_status.config(text="Spinning...", fg="gold")
    outcome, _ = spin_machine(self.machine, self.config, self.bet_amount, save_log=True)
    # ZAČNEMO ANIMACIJO namesto takojšnjega izrisa
    self.animate_spin(outcome["all_spins"], step=0, index=0)

  def finalize_session(self):
    self.balance += self.session_total_win
    self.label_balance.config(text=f"Credit: {self.balance:.2f} €")
    self.btn_spin.config(state="normal", bg="gold")
    self.btn_plus.config(state="normal")
    self.btn_minus.config(state="normal")
    if self.session_total_win > 0:
      self.label_status.config(text=f"Win: {self.session_total_win:.2f} €!", fg="#00ff00")
    else:
      self.label_status.config(text="Ready to spin", fg="gold")

if __name__ == "__main__":
  root = tk.Tk()
  app = SlotMachineGUI(root)
  root.mainloop()