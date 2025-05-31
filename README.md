# NotSoFancyWeather

A weather web application made using FARM tech stack

## Introduction

This is a sample project for a weather app that uses OpenWeatherAPI to get a 3 hours interval weather data. The project contains both the frontend and the backend where we are using React and FastAPI respectively. To store user and weather data, we used MongoDB as our database.

## Getting Started

### 1. Clone Repository

In your terminal run the following git command:

```bash
git clone https://github.com/xer4yx/not-so-fancy-weather
cd not-so-fancy-weather
```

### 2. Create your venv and install dependencies

On your project directory, open the terminal and create a virtual environment:

```bash
python -m venv .venv
```

Activate your virtual env by running:

```bash
./.venv/Scripts/activate
```

Install the required packages from `requirements.txt`

```bash
pip install -r requirements.txt
```

### 3. Create your own `.env` file

For backend, create your own `.env` and refer to ![sample.venv](sample.env) for the declared variables. The `APP_REDIRECT_URL` is your URL for the frontend. If you have a `.env` file for the frontend where the `HOST` and `PORT` are declared, change your `API_REDIRECT_URL` value. If both frontend and backend uses localhost with default port, no need
to change.

For frontend, you must have `REACT_APP_API_HOST` variable which will serve as the variable for the backend URL.

#### NOTE

It is very important that you have your own `.env` file for both frontend and backend since the configs are relying on the variables from the file.

### 4. Run it

For backend:

```bash
python main.py
```

For frontend:

```bash
cd static/app
npm run start
```