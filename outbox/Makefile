.PHONY: help up down setup migrate register-connector update-connector status logs clean test-insert test-update test-delete test-logical-insert consumer consumer-logical

# Default target
help:
	@echo "Available targets:"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo "  make setup           - Full setup: start services, wait, migrate, register connector"
	@echo "  make migrate         - Run database migrations (create customers table)"
	@echo "  make register-connector - Register the Debezium connector"
	@echo "  make update-connector - Update existing connector config"
	@echo "  make restart-connector - Drop slot and restart connector"
	@echo "  make status          - Check status of all services"
	@echo "  make list-topics     - List all Kafka topics"
	@echo "  make logs            - Show logs from all services"
	@echo "  make clean           - Stop services and remove volumes"
	@echo "  make drop-slot        - Drop replication slot (use if connector fails)"
	@echo "  make test-insert     - Insert a test customer"
	@echo "  make test-update     - Update the test customer"
	@echo "  make test-delete     - Delete the test customer"
	@echo "  make test-logical-insert - Emit outbox message via pg_logical_emit_message()"
	@echo "  make consumer        - Start Kafka consumer to view CDC events (table changes)"
	@echo "  make consumer-logical - Start Kafka consumer to view logical messages"

# Start all services
up:
	docker compose up -d
	@echo "Waiting for services to be ready..."
	@make wait-for-services

# Stop all services
down:
	docker compose down

# Wait for services to be ready
wait-for-services:
	@echo "Waiting for PostgreSQL..."
	@for i in $$(seq 1 30); do \
		docker compose exec -T postgres pg_isready -U dbz > /dev/null 2>&1 && break; \
		if [ $$i -eq 30 ]; then \
			echo "PostgreSQL failed to start after 30 seconds"; \
			exit 1; \
		fi; \
		sleep 1; \
	done
	@echo "Waiting for Kafka Connect..."
	@for i in $$(seq 1 30); do \
		curl -s http://localhost:8083/connectors > /dev/null 2>&1 && break; \
		if [ $$i -eq 30 ]; then \
			echo "Kafka Connect failed to start after 30 seconds"; \
			exit 1; \
		fi; \
		sleep 1; \
	done
	@echo "All services are ready!"

# Run database migrations
migrate:
	@echo "Running database migrations..."
	python3 migrations/setup_database.py
	@echo "Migrations completed!"

# Register the Debezium connector
register-connector:
	@echo "Registering Debezium connector..."
	@curl -i -X POST http://localhost:8083/connectors \
		-H "Content-Type: application/json" \
		-d @example-connector.json
	@echo ""
	@echo "Connector registered! Checking status..."
	@sleep 2
	@curl -s http://localhost:8083/connectors/example-connector/status | python3 -m json.tool || echo "Connector may still be starting..."

# Update existing connector config
update-connector:
	@echo "Updating connector config..."
	@curl -i -X PUT http://localhost:8083/connectors/example-connector/config \
		-H "Content-Type: application/json" \
		-d "$$(python3 -c "import json, sys; print(json.dumps(json.load(sys.stdin)['config']))" < example-connector.json)"
	@echo ""
	@echo "Connector updated! Checking status..."
	@sleep 2
	@curl -s http://localhost:8083/connectors/example-connector/status | python3 -m json.tool || echo "Connector may still be starting..."

# Restart connector by dropping slot and restarting task
restart-connector:
	@echo "Pausing connector..."
	@curl -X PUT http://localhost:8083/connectors/example-connector/pause 2>/dev/null || echo "Connector may already be paused"
	@sleep 2
	@echo "Dropping replication slot..."
	@docker compose exec -T postgres psql -U dbz -d example \
		-c "SELECT pg_drop_replication_slot('example_slot');" 2>/dev/null || echo "Slot may not exist or already dropped"
	@echo "Resuming connector (will recreate slot)..."
	@curl -X PUT http://localhost:8083/connectors/example-connector/resume 2>/dev/null || echo "Resume initiated"
	@sleep 3
	@echo "Checking connector status..."
	@curl -s http://localhost:8083/connectors/example-connector/status | python3 -m json.tool

# Full setup: start, migrate, register
setup: up migrate register-connector
	@echo ""
	@echo "✅ Setup complete! Your CDC pipeline is ready."
	@echo ""
	@echo "Try these commands:"
	@echo "  make test-insert  - Insert a test customer"
	@echo "  make consumer     - View CDC events in real-time"

# Check status of services
status:
	@echo "=== Docker Containers ==="
	@docker compose ps
	@echo ""
	@echo "=== Kafka Connect Connectors ==="
	@curl -s http://localhost:8083/connectors | python3 -m json.tool 2>/dev/null || echo "No connectors registered or Kafka Connect not ready"
	@echo ""
	@echo "=== Connector Status ==="
	@curl -s http://localhost:8083/connectors/example-connector/status | python3 -m json.tool 2>/dev/null || echo "Connector not found"
	@echo ""
	@echo "=== Kafka Topics ==="
	@docker compose exec -T kafka /kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list 2>/dev/null || echo "Could not list topics"

# List Kafka topics
list-topics:
	@echo "Kafka topics:"
	@docker compose exec -T kafka /kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# Show logs
logs:
	docker compose logs -f

# Drop replication slot (useful when changing connector config)
drop-slot:
	@echo "Dropping replication slot 'example_slot'..."
	docker compose exec -T postgres psql -U dbz -d example \
		-c "SELECT pg_drop_replication_slot('example_slot');" || echo "Slot may not exist"
	@echo "Slot dropped. Restart the connector to recreate it."

# Clean up everything
clean:
	docker compose down -v
	@echo "All services stopped and volumes removed."

# Test commands
test-insert:
	@echo "Inserting test customer..."
	docker compose exec -T postgres psql -U dbz -d example \
		-c "INSERT INTO customers(name,email) VALUES ('Alice','alice@example.com') RETURNING *;"

test-update:
	@echo "Updating test customer..."
	docker compose exec -T postgres psql -U dbz -d example \
		-c "UPDATE customers SET name='Alice Updated' WHERE id=1 RETURNING *;"

test-delete:
	@echo "Deleting test customer..."
	docker compose exec -T postgres psql -U dbz -d example \
		-c "DELETE FROM customers WHERE id=1;"

test-logical-insert:
	@echo "Emitting outbox message via pg_logical_emit_message()..."
	@echo "This writes directly to the WAL without creating a table row."
	docker compose exec -T postgres psql -U dbz -d example \
		-c "SELECT pg_logical_emit_message(true, 'customers', '{\"op\":\"insert\",\"entity\":\"customer\",\"data\":{\"name\":\"Bob\",\"email\":\"bob@example.com\"}}');"

# Start Kafka consumer to view CDC events
consumer:
	@echo "Starting Kafka consumer. Press Ctrl+C to stop."
	@echo "Waiting for messages from topic: example.public.customers"
	@echo ""
	docker compose exec -T kafka /kafka/bin/kafka-console-consumer.sh \
		--bootstrap-server localhost:9092 \
		--topic example.public.customers \
		--from-beginning

# Start Kafka consumer to view logical messages
consumer-logical:
	@echo "Starting Kafka consumer for logical messages. Press Ctrl+C to stop."
	@echo "Waiting for messages from topic: example.message"
	@echo "Note: Messages are in Debezium format with base64-encoded content"
	@echo ""
	docker compose exec -T kafka /kafka/bin/kafka-console-consumer.sh \
		--bootstrap-server localhost:9092 \
		--topic example.message \
		--from-beginning \
		--property print.key=true \
		--property print.value=true

