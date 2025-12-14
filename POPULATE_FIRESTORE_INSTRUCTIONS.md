To populate your Firestore database with demo data, please follow these steps:

### Prerequisites:
1.  **Firebase Project Setup:** Ensure you have a Firebase project set up and linked to your Google Cloud Project.
2.  **Firebase Authentication Enabled:** Make sure Firebase Authentication is enabled for your project in the Firebase Console. This script will create users directly in Firebase Auth.
3.  **Service Account Key:** You must have a Firebase Admin SDK service account key (a JSON file) downloaded and correctly configured. The `GOOGLE_APPLICATION_CREDENTIALS` environment variable should point to the absolute path of this JSON file.

    Example:
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/firebase-adminsdk.json"
    ```
    (Replace `/path/to/your/firebase-adminsdk.json` with the actual path to your file.)

### Running the Population Script:

1.  **Open your terminal** in the project root directory.
2.  **Run the script** using Python:
    ```bash
    python3 scripts/populate_firestore.py
    ```
    The script will output its progress in the terminal, indicating which users, assets, work orders, etc., are being created.

### Verification:
After the script completes, you can verify the data in your Firebase Console:

1.  Go to the [Firebase Console](https://console.firebase.google.com/).
2.  Select your project.
3.  Navigate to **Authentication** to see the newly created users.
4.  Navigate to **Firestore Database** to see the populated collections (`users`, `assets`, `work_orders`, `parts`, `training_modules`, `user_training`).

**Note:** If you encounter any "permissions denied" errors, double-check that your Firebase service account key has the necessary permissions (e.g., "Cloud Datastore User" or "Firebase Admin SDK Administrator Access") to create and manage data in Firestore and Firebase Authentication.

Let me know once you have successfully populated the database!
