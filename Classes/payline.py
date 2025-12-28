class Payline: 
  def __init__(self, positions: list[int]) -> None:
    self.positions: list[int] = positions
    
  def get_symbol_positions(self, matrix: list[list]) -> list:
    symbols = []
    num_cols = len(matrix[0])
    for col_index, row_index in enumerate(self.positions):
      if col_index >= num_cols:
        break
      symbols.append(matrix[row_index][col_index])
    return symbols
  def is_winning_line(self, reels: list[list[str]], win_condition) -> bool:
    symbols = self.get_symbol_positions(reels)
    return win_condition(symbols)