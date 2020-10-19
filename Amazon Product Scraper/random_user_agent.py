import os
from random import choice

# Join user agents file to the system path
user_agents_file = os.path.join(os.path.dirname(__file__), 'user_agents.txt')


# Utility function to get the user agent
def get_user_agent():
    """
    Load the User Agent File
    """
    user_agent = load_user_agents(uafile=user_agents_file)
    return user_agent


# Utility function to get random UserAgent from the file
def load_user_agents(uafile):
    """
    uafile : string
    path to text file of user agents, one per line
    """
    uas = []

    # read the user agent file and create a list
    with open(uafile, 'rb') as uaf:
        for ua in uaf.readlines():
            if ua:
                uas.append(ua.strip()[1:-1 - 1])

    # return a random user agent
    return choice(uas)
