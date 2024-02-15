# NextGEM.ScoringService
RestAPI service for processing projects (scrape, score with LLMs)

## Endpoints

**GET /status**

Endpoint status and current workload

**GET /scorings/{taskid}**

Information about the state of taskid (processing job).

States: not found, not finished, finished

**POST /score**

Creates a new processing job (scraping, scoring).
Must receive an URL. Additional info is optional.