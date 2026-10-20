from datetime import datetime, timedelta

from rapidfuzz.fuzz import token_set_ratio

# Time window: Pix can pay an order if it arrived between 2h before and 48h after
_BEFORE_WINDOW = timedelta(hours=2)
_AFTER_WINDOW = timedelta(hours=48)


def is_within_time_window(pix_time: datetime, order_time: datetime) -> bool:
    earliest = order_time - _BEFORE_WINDOW
    latest = order_time + _AFTER_WINDOW
    return earliest <= pix_time <= latest


def _expand_initials(bank_name: str, order_name: str) -> str:
    """Expand single-letter tokens in bank_name using tokens from order_name.

    Example: bank 'JOAO P SILVA', order 'JOAO PEDRO SILVA'
    → 'P' matches first letter of 'PEDRO' → expands to 'JOAO PEDRO SILVA'
    """
    bank_tokens = bank_name.split()
    order_tokens = order_name.split()
    expanded = []
    for bt in bank_tokens:
        if len(bt) == 1:
            # Find a matching order token that starts with this letter
            match = next((ot for ot in order_tokens if ot.startswith(bt) and len(ot) > 1), None)
            if match:
                expanded.append(match)
                order_tokens = [ot for ot in order_tokens if ot != match]
                continue
        expanded.append(bt)
    return " ".join(expanded)


def name_score(bank_name: str, order_name: str) -> float:
    if not bank_name or not order_name:
        return 0.0
    expanded = _expand_initials(bank_name, order_name)
    return token_set_ratio(expanded, order_name)
