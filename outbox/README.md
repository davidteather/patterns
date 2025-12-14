# Outbox Pattern with Debezium CDC

Experimenting with PostgreSQL CDC using Debezium and Kafka Connect. This is mostly for my own reference/experimentation.

## Quick Start

```bash
pip install -r requirements.txt
make setup
```

Then test it:
```bash
make consumer  # in one terminal
make test-insert  # in another terminal
```

## Implementation Details

### Setup

The docker compose setup is from this [blog post](https://blog.sequinstream.com/postgres-cdc-with-debezium-complete-step-by-step-tutorial/). I added a Makefile to automate the setup process and a Python migration script to handle the database setup.

The inspiration for this specific approach is from [this blog post](https://www.decodable.co/blog/revisiting-the-outbox-pattern) - using `pg_logical_emit_message()` over a dedicated outbox table. Not convinced it's the best/only way to do the outbox pattern without race conditions, but wanted to try it out.

### What's Included

- **PostgreSQL** with logical replication enabled (`wal_level=logical`)
- **ZooKeeper** + **Kafka** for message streaming
- **Kafka Connect** running the Debezium PostgreSQL connector
- **Makefile** with commands to automate setup, migrations, connector registration, and testing
- **Python migration script** (`migrations/setup_database.py`) that creates the `customers` table and sets `REPLICA IDENTITY FULL`

### Makefile Commands

- `make setup` - Full setup (start services, migrate, register connector)
- `make up/down` - Start/stop services
- `make migrate` - Run database migrations
- `make register-connector` - Register the Debezium connector
- `make status` - Check service/connector status
- `make consumer` - View CDC events in real-time
- `make test-insert/update/delete` - Test database changes
- `make clean` - Stop everything and remove volumes

### Database

The `customers` table has:
- `id` (SERIAL PRIMARY KEY)
- `name` (VARCHAR(255))
- `email` (VARCHAR(255))
- `REPLICA IDENTITY FULL` - needed for full row capture in CDC events

Connection: `postgresql://dbz:dbz@localhost:5432/example?sslmode=disable`

### Connector Config

The Debezium connector (`example-connector.json`) monitors `public.customers` table, uses topic prefix `example`, and creates replication slot `example_slot`.
