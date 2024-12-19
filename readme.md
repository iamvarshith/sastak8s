# FastAPI Cluster Management API

## Overview

_This project implements a Cluster Management API using FastAPI, SQLAlchemy, and RabbitMQ for deployment processing. It provides functionality for user authentication, organization management, cluster creation and resource tracking, and deployment management with resource allocation.
Features_

    User authentication and organization management
    Cluster creation and resource tracking
    Deployment management with resource allocation
    Asynchronous deployment processing using RabbitMQ

Setup

Clone the repository:

    bash
    git clone <repository-url>
    cd <project-directory>

Install dependencies:

    bash
    pip install -r requirements.txt

Set up environment variables:

Create a .env file in the project root and add the following:

    DB_NAME=your_db_name
    SECRET_KEY=your_secret_key
    RABBITMQ_HOST=rabbitmq
    RABBITMQ_PORT=5672
    RABBITMQ_USER=guest
    RABBITMQ_PASSWORD=guest

Initialize the database:

    python
    from app.db.database import init_db
    init_db()

Running the Application
Start the FastAPI server:

    bash
    uvicorn app.main:app --reload

The API will be available at http://localhost:8000.

## API Documentation

Once the server is running, you can access the API documentation at:

* Swagger UI: http://localhost:8000/docs
* ReDoc: http://localhost:8000/redoc

## Testing

Run tests using pytest:

    bash
    pytest

## Project Structure

    
    sastak8s/
    ├── app/
    │   ├── main.py
    │   ├── auth/
    │   ├── clusters/
    │   ├── deployments/
    │   ├── scheduler/
    │   └── db/
    ├── tests/
    ├── Dockerfile
    ├── docker-compose.yml
    ├── requirements.txt
    └── .env

## Deployment

The project includes a Dockerfile and docker-compose.yml for containerized deployment. To run using Docker:

    bash
    docker-compose up --build
