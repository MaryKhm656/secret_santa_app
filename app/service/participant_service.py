from sqlalchemy.orm import Session

from app.db.models import Participant


class ParticipantService:
    @staticmethod
    def user_already_in_game(db: Session, user_id: int, game_id: int) -> bool:
        return (
            db.query(Participant).filter_by(user_id=user_id, game_id=game_id).first()
            is not None
        )

    @staticmethod
    def create_participant(db: Session, user_id: int, game_id: int) -> Participant:
        if ParticipantService.user_already_in_game(db, user_id, game_id):
            raise ValueError("Пользователь уже состоит в этой игре")

        participant = Participant(
            user_id=user_id,
            game_id=game_id,
        )

        db.add(participant)
        db.commit()
        db.refresh(participant)

        return participant
