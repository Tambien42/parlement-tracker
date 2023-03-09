from scrutins import scrutins
from database import connectDB
from groups import groups
from questions import questions
from law_proposals import law_proposals
from commission import commissions

def main():
    scrutins()
    groups()
    questions()
    law_proposals()
    commissions()
    print("done")

if __name__ == '__main__':
    main()