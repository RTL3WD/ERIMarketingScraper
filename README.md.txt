## Getting Started

Follow these steps to set up and run the project locally.

### Prerequisites

```sh
- Python 3.6 or higher
- pip (Python package manager)
- Tesseract-OCR
```

### Installation

1. Clone the repository:

```sh
git clone https://github.com/ERImarketing/Scraper.git
```

2. Create a virtual environment and activate it (recommended):

```sh
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install project dependencies:

```sh
pip install -r requirements.txt
```

4. Set up the database:

python manage.py migrate

### Running the Server

Start the development server:

```sh
python manage.py runserver
```

The server should now be running at `http://127.0.0.1:8000/`.

## Usage

Once the server is running, you can access the web application by opening a web browser and navigating to `http://127.0.0.1:8000/`.

## Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature/fix.
3. Make your changes and commit them.
4. Push your changes to your fork.
5. Submit a pull request.