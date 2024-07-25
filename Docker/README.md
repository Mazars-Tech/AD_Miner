# AD_Miner Docker Setup

This project provides a Docker setup for running AD_Miner with an environment file for setting credentials and various settings. The AD_Miner (miner) container contains a wrapper for the python module/script to automatically fill out the connection and auth arguments.

## Prerequisites

- Docker
- Docker Compose

## File Structure

```
.
├── Docker/
│   ├── Dockerfile
│   ├── ad_miner.sh
│   └── README.md
├── ad_miner/
│   └── ... (AD_Miner source code)
├── docker-compose.yml
├── requirements.txt
├── .env
└── ... (other project files)
```

## Setup and Usage Instructions

1. Clone this repository:
   ```
   git clone https://github.com/Mazars-Tech/AD_Miner && cd AD_Miner
   ```

2. Rename placeholder.env to .env and change the values to something secure.

3. Build the Docker images and start the services:
   ```
   docker compose up -d --build
   ```

4. Check the Bloodhound Container log for initial password or use the below:
   ```
   docker compose logs bloodhound | grep "Initial Password" | awk -F 'Initial Password Set To: ' '{print $2}' | awk '{print $1}'
   ```

5. Browse to the Bloodhound interface and authenticate with email: admin and password as the above, then change the password.

6. Upload Bloodhound data as per usual. Once complete action step 7

7. Run the miner container with the wrapper script:
   ```
   docker-compose exec miner ad_miner.sh report-name-here (you can omit this and a default name will be provided) --rdp --other args 
   ```
   This will run the ad_miner py script with pre-populated connection and auth env vars from the .env file. Your results will be stored in the reports folder, and will be accessible on your host.

## Stopping the Services

To stop all services:
```
docker compose down
```

Or if you want to remove everything:
```
docker compose down -v {you can enter a container name such as `miner` if you just want to remove one service}
```