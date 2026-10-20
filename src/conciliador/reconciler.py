from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from conciliador.matching import is_within_time_window, name_score
from conciliador.models import Order, ReconciliationResult, Transaction
from conciliador.normalization import is_masked_cpf, normalize_name
from conciliador.parsers import parse_extrato_csv, parse_ofx, parse_pedidos_csv

_NAME_THRESHOLD = 80
_VALUE_TOLERANCE = 1.00
_INF_COST = 1e9


def reconcile(
    orders_path: Path,
    statement_path: Path,
) -> list[ReconciliationResult]:
    orders = parse_pedidos_csv(orders_path)
    if str(statement_path).lower().endswith(".ofx"):
        transactions = parse_ofx(statement_path)
    else:
        transactions = parse_extrato_csv(statement_path)
    return _reconcile(orders, transactions)


def _reconcile(
    orders: list[Order],
    transactions: list[Transaction],
) -> list[ReconciliationResult]:
    results: list[ReconciliationResult] = []

    # Separate Pix credits from non-Pix / debits
    pix_credits = [t for t in transactions if t.is_pix_credit]
    ignored = [t for t in transactions if not t.is_pix_credit]

    # Add ignored transactions to results
    for t in ignored:
        results.append(ReconciliationResult(
            order_id="",
            transaction_id=t.id,
            status="ignorado",
            observation=t.description,
        ))

    # Normalize names once
    order_names = [normalize_name(o.client) for o in orders]
    txn_names = [normalize_name(t.payer_name) for t in pix_credits]

    # Build cost matrix for Hungarian algorithm
    n_orders = len(orders)
    n_txns = len(pix_credits)

    if n_orders == 0 or n_txns == 0:
        for o in orders:
            results.append(ReconciliationResult(
                order_id=o.id, transaction_id="", status="pendente",
            ))
        for t in pix_credits:
            results.append(ReconciliationResult(
                order_id="", transaction_id=t.id, status="sem_pedido",
            ))
        return results

    cost = np.full((n_orders, n_txns), _INF_COST)
    scores = np.zeros((n_orders, n_txns))

    for i, order in enumerate(orders):
        for j, txn in enumerate(pix_credits):
            if not is_within_time_window(txn.date, order.date):
                continue
            value_diff = abs(order.value - txn.value)
            if value_diff > _VALUE_TOLERANCE:
                continue
            ns = name_score(txn_names[j], order_names[i])
            scores[i, j] = ns
            # Cost: lower is better. Perfect match = 0, name-only mismatch penalized.
            value_penalty = 0.5 if value_diff > 0.001 else 0.0
            cost[i, j] = (1.0 - ns / 100.0) + value_penalty

    # Run Hungarian algorithm
    row_ind, col_ind = linear_sum_assignment(cost)

    matched_orders: set[int] = set()
    matched_txns: set[int] = set()

    for i, j in zip(row_ind, col_ind):
        if cost[i, j] >= _INF_COST:
            continue  # Not a real match

        order = orders[i]
        txn = pix_credits[j]
        ns = scores[i, j]
        value_exact = abs(order.value - txn.value) < 0.001
        has_name = bool(txn_names[j]) and not is_masked_cpf(txn.payer_name)

        if value_exact and has_name and ns >= _NAME_THRESHOLD:
            status = "conciliado"
        else:
            status = "suspeito"

        results.append(ReconciliationResult(
            order_id=order.id,
            transaction_id=txn.id,
            status=status,
        ))
        matched_orders.add(i)
        matched_txns.add(j)

    # Detect duplicates: unmatched Pix credits that match a conciliado order
    conciliado_map: dict[str, tuple[int, str]] = {}
    for r in results:
        if r.status == "conciliado" and r.order_id:
            idx = next(i for i, o in enumerate(orders) if o.id == r.order_id)
            conciliado_map[r.order_id] = (idx, r.transaction_id)

    for j, txn in enumerate(pix_credits):
        if j in matched_txns:
            continue
        for order_id, (order_idx, _) in conciliado_map.items():
            order = orders[order_idx]
            if not is_within_time_window(txn.date, order.date):
                continue
            if abs(order.value - txn.value) > 0.001:
                continue
            ns = name_score(txn_names[j], order_names[order_idx])
            if ns >= _NAME_THRESHOLD:
                results.append(ReconciliationResult(
                    order_id=order_id,
                    transaction_id=txn.id,
                    status="duplicado",
                ))
                matched_txns.add(j)
                break

    # Unmatched orders → pendente
    for i, order in enumerate(orders):
        if i not in matched_orders:
            results.append(ReconciliationResult(
                order_id=order.id, transaction_id="", status="pendente",
            ))

    # Unmatched Pix credits → sem_pedido
    for j, txn in enumerate(pix_credits):
        if j not in matched_txns:
            results.append(ReconciliationResult(
                order_id="", transaction_id=txn.id, status="sem_pedido",
            ))

    return results
