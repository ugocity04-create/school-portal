"""Grading rules (the usual Nigerian secondary school scheme).
Each subject is out of 100: 1st test 20, 2nd test 20, exam 60.
"""

MAX_CA1 = 20
MAX_CA2 = 20
MAX_EXAM = 60

# (lowest total for the grade, grade, meaning)
BANDS = [
  (75, "A1", "Excellent"),
  (70, "B2", "Very good"),
  (65, "B3", "Good"),
  (60, "C4", "Credit"),
  (55, "C5", "Credit"),
  (50, "C6", "Credit"),
  (45, "D7", "Pass"),
  (40, "E8", "Pass"),
  (0, "F9", "Fail"),
]

def total_of(ca1, ca2, exam):
  """Total marks, or None until all three parts are entered."""
  if ca1 is None or ca2 is None or exam is None:
    return None
  return round(ca1 + ca2 + exam, 1)

def grade_for(total):
  """(grade, meaning) for a total, or (None, None) if there is no total yet."""
  if total is None:
    return None, None
  for lowest, grade, meaning in BANDS:
    if total >= lowest:
      return grade, meaning
    return "F9", "Fail"
  
def parse_score(value, maximum):
  """Turn what a teacher typed into a number. Return (value, error).
  An empty box means 'not entered yet' and is allowed.
  """
  if value is None:
    return None, None
  text = str(value).strip()
  if text == "":
    return None, None
  try:
    number = float(text.replace(",", "."))
  except ValueError:
    return None, "Enter a Number"
  if number != number or number in (float("inf"), float("-inf")):
    return None, "Enter a number"
  if number < 0 or number > maximum:
    return None, "Must be between 0 and %d" % maximum
  return round(number, 1), None