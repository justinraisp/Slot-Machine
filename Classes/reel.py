from Classes.symbol import Symbol
class Reel: 
  def __init__(self, symbols: list[Symbol]) -> None:
    self.symbols: list[Symbol] = symbols
    self.count: int = len(symbols)
    
  def get_symbols(self, stop_position: int, height: int) -> list[Symbol]:
    result = []
    for i in range(height):
      result.append(self.symbols[(stop_position + i) % self.count])
    return result
  