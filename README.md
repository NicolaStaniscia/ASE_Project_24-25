# ASE_Project_24-25

## Getting Started

### INTEGRATION TESTS

To execute tests for the entire service, navigate to the `/src` directory and run the following command:

```bash
docker compose up --build
```
 
Once the command executes successfully, you can run all application test collections using Postman. These collections are located in the directory:
`/docs/postman/Integration_tests/`.

### ISOLATION TESTS

To test the microservices in isolation, go to the `/src/Isolation_Tests` directory.
Within this directory, you’ll find sub-directories corresponding to each microservice.

To test a specific microservice:

1. Navigate to the appropriate sub-directory.
2. Run the script:

   ```run.sh```

3. Wait until the container is built successfully.

Once the microservice is running, you can use Postman to execute the corresponding isolation test collection for the specific microservice. These collections are located in:
`/docs/postman/Isolation_tests/`.

**Warning**:
After finishing the isolated test, you must stop the container and execute the script: ```clean.sh``` to avoid port conflicts.

### LOCUST

The Locust tests are located in the `/docs/locust/` directory and are divided into:

- Locust User
- Locust Admin

To execute the test:

1. Select one of the two directories.

2. Create a Python virtual environment using the command:

   ```bash
   python3 -m venv venv
   ```

3. Activate the environment:

   ```bash
   source venv/bin/activate
   ```

4. Install the dependencies using the command:

   ```bash
   pip install -r requirements.txt
   ```

5. Run Locust using the command:

   ```bash
   locust
   ```

   Then, open a browser and enter the URL: http://localhost:8089.

6. Configure the test by setting:

    - The number of users.
    - The rate of users connecting per second.
    - The server address to test (https://localhost:8080 for users and https://localhost:8081 for admins).
    - The runtime duration (e.g., 1m for 1 minute).

    At the end of the execution, Locust will generate a report providing insights into the application's performance.

**Warning**:

- The commands for creating and activating the virtual environment are specific to Linux operating systems.
- It is strongly recommended to first run the Locust User test and then the Locust Admin test. Admins have database modification functions that might alter user test results.