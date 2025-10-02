#!/bin/bash
# PostgreSQL Data Import Script
# Run this script to import all CSV data into PostgreSQL

set -e  # Exit on any error

# Database connection details
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="chatterfix_cmms"
DB_USER="postgres"

echo "Starting data import..."


# Import users
echo "Importing users..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy users FROM 'users.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import locations
echo "Importing locations..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy locations FROM 'locations.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import suppliers
echo "Importing suppliers..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy suppliers FROM 'suppliers.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import assets
echo "Importing assets..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy assets FROM 'assets.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import work_orders
echo "Importing work_orders..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy work_orders FROM 'work_orders.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import parts
echo "Importing parts..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy parts FROM 'parts.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import pm_templates
echo "Importing pm_templates..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy pm_templates FROM 'pm_templates.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import maintenance_schedules
echo "Importing maintenance_schedules..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy maintenance_schedules FROM 'maintenance_schedules.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import sensor_readings
echo "Importing sensor_readings..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy sensor_readings FROM 'sensor_readings.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import ai_predictions
echo "Importing ai_predictions..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy ai_predictions FROM 'ai_predictions.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import purchase_orders
echo "Importing purchase_orders..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy purchase_orders FROM 'purchase_orders.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import po_line_items
echo "Importing po_line_items..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy po_line_items FROM 'po_line_items.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import inventory_transactions
echo "Importing inventory_transactions..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy inventory_transactions FROM 'inventory_transactions.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import attachments
echo "Importing attachments..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy attachments FROM 'attachments.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import audit_log
echo "Importing audit_log..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy audit_log FROM 'audit_log.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import media_files
echo "Importing media_files..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy media_files FROM 'media_files.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import ocr_results
echo "Importing ocr_results..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy ocr_results FROM 'ocr_results.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import speech_transcriptions
echo "Importing speech_transcriptions..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy speech_transcriptions FROM 'speech_transcriptions.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import ai_model_configs
echo "Importing ai_model_configs..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy ai_model_configs FROM 'ai_model_configs.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import ai_request_logs
echo "Importing ai_request_logs..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy ai_request_logs FROM 'ai_request_logs.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import model_fine_tuning
echo "Importing model_fine_tuning..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy model_fine_tuning FROM 'model_fine_tuning.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import model_ab_tests
echo "Importing model_ab_tests..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy model_ab_tests FROM 'model_ab_tests.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import ai_prompt_templates
echo "Importing ai_prompt_templates..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy ai_prompt_templates FROM 'ai_prompt_templates.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

# Import ai_alerts
echo "Importing ai_alerts..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\copy ai_alerts FROM 'ai_alerts.csv' WITH (FORMAT csv, HEADER true, QUOTE '"', ESCAPE '"');"

echo "Data import completed successfully!"
echo "Updating sequences for SERIAL columns..."

# Update sequences for SERIAL primary keys

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('locations_id_seq', COALESCE((SELECT MAX(id) FROM locations), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('suppliers_id_seq', COALESCE((SELECT MAX(id) FROM suppliers), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('assets_id_seq', COALESCE((SELECT MAX(id) FROM assets), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('work_orders_id_seq', COALESCE((SELECT MAX(id) FROM work_orders), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('parts_id_seq', COALESCE((SELECT MAX(id) FROM parts), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('pm_templates_id_seq', COALESCE((SELECT MAX(id) FROM pm_templates), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('maintenance_schedules_id_seq', COALESCE((SELECT MAX(id) FROM maintenance_schedules), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('sensor_readings_id_seq', COALESCE((SELECT MAX(id) FROM sensor_readings), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('ai_predictions_id_seq', COALESCE((SELECT MAX(id) FROM ai_predictions), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('purchase_orders_id_seq', COALESCE((SELECT MAX(id) FROM purchase_orders), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('po_line_items_id_seq', COALESCE((SELECT MAX(id) FROM po_line_items), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('inventory_transactions_id_seq', COALESCE((SELECT MAX(id) FROM inventory_transactions), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('attachments_id_seq', COALESCE((SELECT MAX(id) FROM attachments), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('audit_log_id_seq', COALESCE((SELECT MAX(id) FROM audit_log), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('ocr_results_id_seq', COALESCE((SELECT MAX(id) FROM ocr_results), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('speech_transcriptions_id_seq', COALESCE((SELECT MAX(id) FROM speech_transcriptions), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('ai_model_configs_id_seq', COALESCE((SELECT MAX(id) FROM ai_model_configs), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('ai_request_logs_id_seq', COALESCE((SELECT MAX(id) FROM ai_request_logs), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('model_fine_tuning_id_seq', COALESCE((SELECT MAX(id) FROM model_fine_tuning), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('model_ab_tests_id_seq', COALESCE((SELECT MAX(id) FROM model_ab_tests), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('ai_prompt_templates_id_seq', COALESCE((SELECT MAX(id) FROM ai_prompt_templates), 1));"

psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT setval('ai_alerts_id_seq', COALESCE((SELECT MAX(id) FROM ai_alerts), 1));"

echo "All sequences updated!"
