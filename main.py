from bot import client
from config import *
import bale
import os

def main():
    logger.info("Starting the bot...")
    
    client.run_bot()

if __name__ == "__main__":
    main()