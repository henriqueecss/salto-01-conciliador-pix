from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    id: str
    date: datetime
    client: str
    items: str
    value: float
    channel: str


@dataclass
class Transaction:
    id: str
    date: datetime
    description: str
    value: float
    payer_name: str
    is_pix_credit: bool


@dataclass
class ReconciliationResult:
    order_id: str
    transaction_id: str
    status: str  # conciliado, suspeito, duplicado, pendente, sem_pedido, ignorado
    observation: str = ""
