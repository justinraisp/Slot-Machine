from Classes.symbol import Symbol
from typing import List, Optional

class SymbolWindow:
  def __init__(self, width: int, height: int):
    self.width: int = width
    self.height: int = height
    self.symbols: List[List[Optional[Symbol]]] = [
      [None for _ in range(width)]
      for _ in range(height)
    ]

  def add_symbol(self, symbol: Symbol, row: int, col: int) -> None:
    self.symbols[row][col] = symbol

  def get_symbol(self, row: int, col: int) -> Symbol:
    return self.symbols[row][col]

  def getMatrix(self) -> List[List[Optional[Symbol]]]:
    return self.symbols
