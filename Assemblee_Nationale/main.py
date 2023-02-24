from scrutins import scrutins
from database import connectDB
from groups import groups
from questions import questions
from law_proposals import law_proposals

def main():
    # Your code here
    scrutins()
    groups()
    questions()
    law_proposals()
    print("done")

if __name__ == '__main__':
    main()