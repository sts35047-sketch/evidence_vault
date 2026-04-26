# Evidence Service

## Overview
The Evidence Service is a web application designed to manage and process evidence files securely. It provides functionalities for file storage, encryption, and auditing, ensuring that sensitive information is handled appropriately.

## Features
- File upload and download
- Encryption and decryption of files using Fernet
- Audit logging for tracking actions within the application
- API endpoints for interacting with the service

## Project Structure
```
evidence-service
├── src
│   ├── app.py                # Entry point of the application
│   ├── api                   # API package
│   │   ├── __init__.py
│   │   └── v1                # Version 1 of the API
│   │       ├── __init__.py
│   │       └── routes.py
│   ├── core                  # Core functionalities
│   │   ├── config.py         # Configuration settings
│   │   └── security.py       # Security functions
│   ├── db                    # Database setup and models
│   │   ├── base.py
│   │   └── models.py
│   ├── services              # Service layer for business logic
│   │   ├── storage.py        # File storage operations
│   │   └── encryption.py     # Encryption functionalities
│   ├── tasks                 # Background tasks
│   │   └── worker.py
│   ├── audit                 # Audit logging
│   │   └── logger.py
│   └── types                 # Data schemas
│       └── schemas.py
├── migrations                 # Database migrations
│   └── init_sqlite.sql
├── tests                     # Unit tests
│   ├── test_encryption.py
│   ├── test_upload.py
│   └── test_audit.py
├── requirements.txt          # Project dependencies
├── pyproject.toml            # Project configuration
├── .env.example              # Example environment variables
└── README.md                 # Project documentation
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd evidence-service
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the database:
   - Run the migration SQL against your `evidence.db`:
     ```
     sqlite3 evidence.db < migrations/init_sqlite.sql
     ```

4. Configure environment variables:
   - Copy `.env.example` to `.env` and set the necessary variables, including `FERNET_KEY` for file encryption. Generate a key using:
     ```python
     from cryptography.fernet import Fernet
     print(Fernet.generate_key().decode())
     ```

5. Run the application:
   ```
   python src/app.py
   ```

## Testing
To run the unit tests, use:
```
pytest tests/
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.