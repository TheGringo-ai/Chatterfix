# ChatterFix CMMS (Consolidated)

This is the consolidated version of the ChatterFix CMMS application, combining the best features from previous iterations into a single, unified codebase.

## Features

-   **Unified Interface:** Consistent styling and navigation across all modules.
-   **Work Order Management:** Create, update, and track work orders with a modern UI.
-   **AI Integration:** Built-in AI assistant for querying CMMS data and getting help.
-   **Predictive Maintenance:** (Optional) ML-powered engine to predict asset failures.
-   **Health Monitoring:** System health checks and SLO tracking.
-   **Revolutionary AI Dashboard:** A futuristic dashboard for high-level insights.

## Directory Structure

-   `main.py`: The entry point of the application (FastAPI).
-   `unified_cmms_system.py`: Shared UI components and styles.
-   `revolutionary_ai_dashboard.py`: Advanced AI dashboard module.
-   `predictive_engine.py`: Predictive maintenance logic.
-   `health_monitor.py`: System health monitoring.
-   `navigation_component.py`: Navigation bar component.

## Setup and Running

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Application:**
    ```bash
    python main.py
    ```
    Or using uvicorn directly:
    ```bash
    uvicorn main:app --reload
    ```

3.  **Access the App:**
    Open your browser and navigate to `http://localhost:8000`.

## Configuration

-   **Database:** By default, the app uses a local SQLite database in `./data/cmms.db` (if `/var/lib` is not writable).
-   **Port:** Default port is 8000. You can change it via the `CMMS_PORT` environment variable.
