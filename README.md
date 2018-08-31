## Cairo Congestion

The Cairo Congestion Project is a ...

The crawler was run on Docker containers on top of an AWS EC2 instance. It uses the Google Directions API to regularly collect data and stores it in a MongoDB server contained in a connected Docker container. A .csv file is created and stored in the project directory every day, which contains all the collected data of that day.

How to access and run project:
    1. Clone this project.
    2. Go to the directory of the cloned project.
    3. Run docker-compose up to schedule and run the crawler.
