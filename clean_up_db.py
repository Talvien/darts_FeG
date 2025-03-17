from models import db, Player, Tournament, Group, GroupPlayer, Round, Match
from app import app

def clean_database_except_player():
    with app.app_context(): 
        try:
            # Delete all entries from tables except for Player
            db.session.query(Match).delete()
            db.session.query(GroupPlayer).delete()
            db.session.query(Group).delete()
            db.session.query(Round).delete()
            db.session.query(Tournament).delete()
            
            db.session.commit()
            print("Database cleaned successfully, only Player table remains intact.")
        except Exception as e:
            db.session.rollback()
            print(f"Error cleaning database: {e}")

# Call the function to clean the database
clean_database_except_player()
