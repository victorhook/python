from bs4 import BeautifulSoup as bs4
import requests
import re
import threading
import time
import sys

URL_BASE      = 'http://voto.se/'
LABEL_PATTERN = '(?<=top">)(.*?)(?=<\/label>)'
DEFAULT_VOTES = 10

# Sends a vote to the given vote number!
def send_vote(poll_name, vote_nbr):
    requests.post(URL_BASE + '/poll/saveAnswer', 
        data={'key': poll_name, 'answervalue1': vote_nbr})


if __name__ == "__main__":

    """ Need arguments: 
        - Vote name
        - Vote number (whom you want to vote on, starting at 0)
        - Optional: Number of votes (default is 10)
    """

    if len(sys.argv) < 3:
        # Not enough arguments, exit!
        print('Enter name of poll, and which number you want to vote on')
        sys.exit(0)

    poll_name     = sys.argv[1]
    vote_nbr      = int(sys.argv[2])
    desired_votes = int(sys.argv[3]) if len(sys.argv) == 4 else DEFAULT_VOTES

    url = URL_BASE + poll_name

    # Scrape the vote options for some nice output (Not needed for voting though)
    request = requests.get(URL_BASE + poll_name).content.__str__()
    vote_options = re.compile(LABEL_PATTERN).findall(request)

    # Ensure that the vote number is within the correct range
    if vote_nbr < 0 or vote_nbr > len(vote_options):
        print("You can't vote for that!")
        sys.exit(0)

    votes = []

    for i in range(desired_votes):
        vote = threading.Thread(target=send_vote, args=(poll_name, vote_nbr))
        votes.append(vote)

    # Voting started!
    print('Voting %s times on %s!' % (desired_votes, vote_options[vote_nbr]))
        
    for vote in votes:
        vote.start()

    # Wait until all votes are finished
    for vote in votes:
        vote.join()

    print('Done!')



