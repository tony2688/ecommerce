# skeleton
@startuml
title Saga de Checkout: Idempotencia + Pagos MP + Inventario + Notificaciones

actor Buyer
participant "Frontend (Jinja+htmx)" as FE
participant "API (FastAPI)" as API
participant "MySQL" as DB
participant "Redis/Celery" as Q
participant "Mercado Pago" as MP
participant "Email/Push" as NOTIF

== Inicio ==
Buyer -> FE : Iniciar Checkout
FE -> API : POST /checkout/start\n(Idempotency-Key)
API -> DB : INSERT idempotency_key (if new)
API -> DB : CREATE order(status=PENDING)\nRESERVE stock (optimistic locking)\nWRITE outbox_event(order_created)
DB --> API : OK
API -> Q : Enqueue outbox publisher
API --> FE : 200 {order_id}

== Crear intención de pago ==
FE -> API : POST /payments/mp/intent\n(Idempotency-Key)
API -> MP : Crear preferencia/brick
MP --> API : payment_id / init_point
API -> DB : SAVE payment(intent), map order<->payment
API --> FE : 200 {payment_url|brick_token}

== Webhook de MP (aprobado / rechazado) ==
MP -> API : POST /webhooks/mercadopago
API -> DB : UPSERT webhook_event(event_id)  <<IDEMP>>
API -> MP : GET /payments/{id} (verify)
MP --> API : estado {approved|rejected|in_process}
API -> DB : UPDATE payment.status
alt approved
  API -> DB : CONFIRM stock (commit reserved)\nUPDATE order: CONFIRMED\nWRITE outbox_event(order_confirmed)
  API -> Q : Enqueue notifications (email/push) <<IDEMP notification_key>>
else rejected
  API -> DB : RELEASE stock\nUPDATE order: CANCELED\nWRITE outbox_event(order_canceled)
end
API --> MP : 200 OK (always)

== Publicación outbox ==
Q -> DB : Fetch outbox_event WHERE status=PENDING
Q -> NOTIF : Send email/push
NOTIF --> Q : OK/Fail
alt OK
  Q -> DB : UPDATE outbox_event: PUBLISHED
else Fail
  Q -> DB : UPDATE outbox_event: FAILED, retry_count++, next_retry_at
end
@enduml

@startuml
title Proceso Outbox: Publicación confiable con reintentos

participant "Transacción de Negocio" as TX
database "MySQL" as DB
participant "Worker Publisher (Celery)" as PUB
queue "Redis" as R

== Escritura Outbox en la misma transacción ==
TX -> DB : BEGIN
TX -> DB : UPDATE dominio (p.ej. order/status)\nINSERT outbox_event(status=PENDING)
TX -> DB : COMMIT

== Publicación asíncrona ==
PUB -> DB : SELECT next PENDING outbox_event FOR UPDATE SKIP LOCKED
alt evento recuperado
  PUB -> R : Publish/Enqueue message
  R --> PUB : ACK/NACK
  alt ACK
    PUB -> DB : UPDATE outbox_event: PUBLISHED
  else NACK/Timeout
    PUB -> DB : UPDATE outbox_event: FAILED\nretry_count++, next_retry_at (backoff)
  end
else sin eventos
  PUB -> PUB : Sleep small interval
end
@enduml

