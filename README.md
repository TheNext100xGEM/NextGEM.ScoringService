# NextGEM.ScoringService
RestAPI service for processing projects (scrape, score with LLMs)

## API keys and DB URI

API keys should be provided in ```config.json``` file! Format:
```
{
    "OPENAI_API_KEY": "key",
    "GEMINI_API_KEY": "key",
    "MISTRAL_API_KEY": "key",
    "mongo_uri": "uri"
}
```


## Endpoints

Detailed description in Swagger specification

**GET /status**: Endpoint status and current workload

**POST /score**: Creates a new processing job (scraping, scoring).

**GET /scorings/{taskid}**: Information about the state of taskid (processing job).
