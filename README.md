## This repository is composed of the following small projects:

1. Weather notifier
    - Gets hourly forecast data for the day, formats the % chance of rain and temperature data as a table and sends the formatted text as a slack message.  
    - If at any time of the day there is a % chance of rain higher than a certain threshold, relevant parties will be tagged in the message.
    - This uses python's polars library to manipulate the data pulled from [Open-Meteo](https://open-meteo.com/)'s and Slack's api to send messages.
2. Vocab helper  
    - Gets a random, previously unseen word from a set stored in a database and sends the word's meaning, usage, and example sentences with translations to a slack channel.   
    - Each user gets their own list so they get tagged for every word that gets sent to the channel. 
    - This is powered by a django rest framework app that has an endpoint that gets post requests from a cron job. Formatted messages are sent using slack's api.
3. Bus location notifier
    - Provides the current location of all buses (Yokohama city buses to be more specific) in a given route. 
    - The bus route number gets sent to a FastAPI endpoint via a GET request. Playwright library is used to navigate to specific urls and locate bus locations.
    