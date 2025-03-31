# Error Code Taxonomy

This document defines the error codes used for structured logging within the project.

## Code Ranges

| Code Range | Category                  | Description                                        |
| :--------- | :------------------------ | :------------------------------------------------- |
| 1000-1999  | Network Errors            | Errors related to fetching resources over HTTP.    |
| 2000-2999  | SVG Parsing Errors        | Errors encountered during SVG file analysis.       |
| 3000-3999  | Mermaid Generation Errors | Errors during the conversion from SVG to Mermaid.  |
| 4000-4999  | Fallback Handling         | Issues related to fallback mechanisms.             |
| 5000-5999  | File I/O Errors           | Errors related to reading or writing files.        |
| 6000-6999  | Input Processing Errors   | Errors related to parsing the input markdown tree. |
| 7000-7999  | Content Extraction Errors | Errors during HTML parsing or content extraction.  |
| 9000-9999  | General/Unknown Errors    | Catch-all for unexpected or uncategorized errors.  |

## Specific Codes (Examples)

### Network Errors (1xxx)

| Code | Name            | Description                                      | Severity |
| :--- | :-------------- | :----------------------------------------------- | :------- |
| 1001 | Timeout         | Request timed out while fetching a resource.     | WARN     |
| 1002 | ConnectionError | Could not establish a connection to the server.  | ERROR    |
| 1003 | HTTPError       | Received an HTTP error status code (4xx or 5xx). | WARN     |
| 1004 | SSLError        | SSL certificate verification failed.             | ERROR    |
| 1005 | URLRequired     | A required URL was missing or invalid.           | ERROR    |

### SVG Parsing Errors (2xxx)

| Code | Name               | Description                                     | Severity |
| :--- | :----------------- | :---------------------------------------------- | :------- |
| 2001 | InvalidXML         | SVG file is not valid XML.                      | ERROR    |
| 2002 | MissingRootElement | SVG root element (`<svg>`) not found.           | ERROR    |
| 2003 | ElementParsing     | Error parsing a specific SVG element.           | WARN     |
| 2004 | InvalidPathData    | SVG path data (`d` attribute) is malformed.     | WARN     |
| 2005 | UnsupportedFeature | SVG uses a feature not supported by the parser. | WARN     |

### Mermaid Generation Errors (3xxx)

| Code | Name             | Description                                       | Severity |
| :--- | :--------------- | :------------------------------------------------ | :------- |
| 3001 | ConversionFailed | General failure during SVG to Mermaid conversion. | ERROR    |
| 3002 | LayoutFailure    | Mermaid could not determine a valid layout.       | WARN     |
| 3003 | SyntaxError      | Generated Mermaid syntax is invalid.              | ERROR    |
| 3004 | MissingData      | Required data for conversion was missing.         | WARN     |

### Fallback Handling (4xxx)

| Code | Name              | Description                                       | Severity |
| :--- | :---------------- | :------------------------------------------------ | :------- |
| 4001 | RefPreservation   | Fallback: Preserved original SVG reference.       | INFO     |
| 4002 | AltTextGeneration | Fallback: Generated alternative text description. | INFO     |
| 4003 | FallbackFailed    | The fallback mechanism itself failed.             | ERROR    |

### File I/O Errors (5xxx)

| Code | Name              | Description                                  | Severity |
| :--- | :---------------- | :------------------------------------------- | :------- |
| 5001 | ReadError         | Could not read from a file.                  | ERROR    |
| 5002 | WriteError        | Could not write to a file.                   | ERROR    |
| 5003 | PermissionDenied  | Insufficient permissions for file operation. | ERROR    |
| 5004 | FileNotFoundError | The specified file does not exist.           | ERROR    |

### Input Processing Errors (6xxx)

| Code | Name               | Description                                        | Severity |
| :--- | :----------------- | :------------------------------------------------- | :------- |
| 6001 | InvalidInputURL    | The provided input URL is invalid or inaccessible. | ERROR    |
| 6002 | MarkdownParseError | Failed to parse the input markdown tree file.      | ERROR    |
| 6003 | URLExtractionError | Failed to extract URLs from the markdown tree.     | ERROR    |

### Content Extraction Errors (7xxx)

| Code | Name              | Description                                    | Severity |
| :--- | :---------------- | :--------------------------------------------- | :------- |
| 7001 | HTMLParseError    | Failed to parse the HTML content of a webpage. | WARN     |
| 7002 | ContentNotFound   | Could not find expected content on the page.   | WARN     |
| 7003 | URLReplacementErr | Failed to replace relative URLs.               | WARN     |

_(This list is not exhaustive and will be expanded as needed.)_
