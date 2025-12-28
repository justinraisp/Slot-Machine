class Symbol:
  def __init__(self, name: str, is_scatter: bool = False, is_wild: bool = False) -> None:
      self.name: str = name
      self.is_scatter: bool = is_scatter
      self.is_wild: bool = is_wild
    
  def __repr__(self):
    return f"{self.name}"
  
  def copy(self):
    return Symbol(self.name, self.is_scatter, self.is_wild)

  def equals(self, other: 'Symbol') -> bool:
    return self.name == other.name and self.is_scatter == other.is_scatter and self.is_wild == other.is_wild