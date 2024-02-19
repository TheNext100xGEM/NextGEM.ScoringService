# NextGEM.ScoringService
RestAPI service for processing projects (scrape, score with LLMs)

## Endpoints

Detailed description in Swagger specification

**GET /status**: Endpoint status and current workload

**POST /score**: Creates a new processing job (scraping, scoring).

**GET /scorings/{taskid}**: Information about the state of taskid (processing job).
