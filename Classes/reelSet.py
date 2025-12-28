from Classes.reel import Reel
class ReelSet: 
  def __init__(self, reels: list[Reel], weight: float) -> None:
    self.reels: list[Reel] = reels
    self.weight: float = weight