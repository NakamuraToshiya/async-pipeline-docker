# CloudWatch Logs Insights Queries

Target log groups:
- /ecs/pipeline-api
- /ecs/pipeline-worker

## 1. Error Logs (ERROR only)
fields @timestamp, service, job_id, status_code, error_type, error, message
| filter level = "ERROR"
| sort @timestamp desc
| limit 50

## 2. Trace a Specific job_id
fields @timestamp, service, level, message, message_id, s3_key, error
| filter job_id = "<job_id>"
| sort @timestamp asc

## 3. Count by Service and Level
stats count() by service, level
| sort count desc

## 4. Error Trend Over Time (1-minute bins)
filter level = "ERROR"
| stats count() as error_count by bin(1m), service
| sort @timestamp desc
