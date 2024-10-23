# Catalog Management System API Documentation

## Overview
This document provides comprehensive documentation for the Catalog Management System API, which handles catalog data processing, manufacturer management, and real-time synchronization.

## Database Models

### Manufacturer
```python
{
    "id": integer,
    "name": string,
    "brands": array[Brand]
}
```

### Brand
```python
{
    "id": integer,
    "name": string,
    "manufacturer_id": integer,
    "manufacturer": Manufacturer
}
```

### Catalog
```python
{
    "id": integer,
    "name": string,
    "article_code": string,
    "barcode": string,
    "brand_id": integer,
    "description": string,
    "price": float,
    "created_at": datetime,
    "updated_at": datetime
}
```

## Services

### Manufacturer Service
Located in `services/manufacturer_service.py`

#### Methods:
1. `add_manufacturer(name: str) -> tuple[bool, str]`
   - Adds a new manufacturer to the system
   - Parameters:
     - name: Manufacturer name
   - Returns: Success status and message

2. `add_brand(name: str, manufacturer_id: int) -> tuple[bool, str]`
   - Adds a new brand and links it to a manufacturer
   - Parameters:
     - name: Brand name
     - manufacturer_id: ID of the parent manufacturer
   - Returns: Success status and message

3. `get_manufacturers() -> List[Dict]`
   - Retrieves all manufacturers and their associated brands
   - Returns: List of manufacturer dictionaries with nested brand information

### Catalog Service
Located in `services/catalog_service.py`

#### Methods:
1. `add_catalog_entries(df: pd.DataFrame) -> tuple[bool, str]`
   - Adds new catalog entries from a pandas DataFrame
   - Parameters:
     - df: DataFrame containing catalog entries
   - Returns: Success status and message

2. `get_catalogs() -> List[Dict]`
   - Retrieves all catalog entries
   - Returns: List of catalog dictionaries

### FTP Service
Located in `services/ftp_service.py`

#### Methods:
1. `connect() -> tuple[bool, str]`
   - Establishes FTP connection
   - Returns: Connection status and message

2. `disconnect()`
   - Closes FTP connection

3. `list_files(directory: str = "") -> tuple[bool, List[str], str]`
   - Lists files in the specified directory
   - Parameters:
     - directory: Target directory path
   - Returns: Success status, file list, and message

4. `download_file(remote_path: str) -> tuple[bool, pd.DataFrame, str]`
   - Downloads and processes file from FTP server
   - Parameters:
     - remote_path: Path to remote file
   - Returns: Success status, processed DataFrame, and message

### Sync Service
Located in `services/sync_service.py`

#### Methods:
1. `register(websocket)`
   - Registers a new WebSocket client
   - Parameters:
     - websocket: WebSocket connection object

2. `unregister(websocket)`
   - Unregisters a WebSocket client
   - Parameters:
     - websocket: WebSocket connection object

3. `broadcast(message: Dict)`
   - Broadcasts message to all connected clients
   - Parameters:
     - message: Message dictionary to broadcast

4. `check_for_updates()`
   - Checks for catalog updates with retry mechanism
   - Returns: Update status and statistics

## WebSocket API
Located in `services/websocket_handler.py`

### Connection
- WebSocket URL: `ws://0.0.0.0:8765`
- Protocol: WebSocket (ws://)

### Message Types:
1. Connection Status
```json
{
    "type": "connection",
    "message": string,
    "timestamp": string,
    "client_count": integer
}
```

2. Update Notification
```json
{
    "type": "update",
    "message": string,
    "timestamp": string,
    "stats": {
        "total_records": integer,
        "recent_updates": integer
    }
}
```

3. Error Notification
```json
{
    "type": "error",
    "message": string,
    "timestamp": string
}
```

4. Status Update
```json
{
    "type": "status",
    "message": string,
    "timestamp": string,
    "stats": {
        "total_records": integer,
        "recent_updates": integer
    }
}
```

## Data Validation

### Validators
Located in `utils/validators.py`

1. `validate_ean13(barcode: str) -> bool`
   - Validates EAN-13 barcode format
   - Parameters:
     - barcode: String to validate
   - Returns: Boolean indicating validity

2. `validate_article_code(code: str) -> bool`
   - Validates article code format
   - Parameters:
     - code: String to validate
   - Returns: Boolean indicating validity

3. `validate_required_fields(data: dict) -> tuple[bool, list]`
   - Validates required catalog fields
   - Parameters:
     - data: Dictionary containing field data
   - Returns: Validation status and list of missing fields

## Data Processing

### Processors
Located in `utils/processors.py`

1. `process_file(file, file_type: str, column_mapping: Dict[str, str] = None) -> tuple[pd.DataFrame, bool, str]`
   - Processes uploaded files (CSV or Excel)
   - Parameters:
     - file: File object
     - file_type: Type of file ('csv' or 'excel')
     - column_mapping: Optional column mapping dictionary
   - Returns: Processed DataFrame, success status, and message

2. `standardize_catalog_data(df: pd.DataFrame) -> pd.DataFrame`
   - Standardizes catalog data format
   - Parameters:
     - df: Input DataFrame
   - Returns: Standardized DataFrame

## Error Handling
All API endpoints include error handling with appropriate error messages and HTTP status codes. Common error scenarios:

1. Database Connection Errors
2. Validation Errors
3. File Processing Errors
4. FTP Connection Errors
5. WebSocket Connection Errors

## Security Considerations
1. Database credentials are managed through environment variables
2. FTP credentials are not stored persistently
3. WebSocket connections include periodic health checks
4. Input validation is performed on all data entry points

## Rate Limiting
The sync service includes built-in retry mechanisms with exponential backoff:
- Maximum retry attempts: 3
- Base delay: 4 seconds
- Maximum delay: 10 seconds
