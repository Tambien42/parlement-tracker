from scrutins import scrutins
from database import connectDB
from groups import groups
from questions import questions
from law_proposals import law_proposals
from commission import commissions
from deputes import deputes

def main():
    groups()
    commissions([], None, False)
    scrutins('')
    questions('')
    law_proposals('')
    deputes([])
    print("done")

if __name__ == '__main__':
    main()