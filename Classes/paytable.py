class Paytable:
  def __init__(self):
    self.rules: dict[tuple[str, int], dict] = {}

  def add_rule(self, symbol_name: str, count: int, rule: dict) -> None:
    self.rules[(symbol_name, count)] = rule

  def get_payout(self, symbol_name: str, count: int) -> float:
    rule = self.rules.get((symbol_name, count))
    return rule.get("payout", 0) if rule else 0

  def get_rule(self, symbol_name: str, count: int) -> dict:
    return self.rules.get((symbol_name, count), {})
