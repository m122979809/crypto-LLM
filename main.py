import time
import datetime
import configparser
from .dataCollection.coindesk import fetch_and_save_news_to_csv

# Run the program
if __name__ == '__main__':
    fetch_and_save_news_to_csv()
