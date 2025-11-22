from typing import List

from sqlalchemy.orm import Session

from app.db.models import Game, Participant, User


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

    @staticmethod
    def get_all_participant_by_game(
        db: Session, game_id: int, organizer_id: int
    ) -> List[Participant]:
        game = db.get(Game, game_id)
        if not game:
            raise ValueError("Игра не найдена")

        organizer = db.get(User, organizer_id)
        if not organizer:
            raise ValueError("Пользователь не найден")

        if game.organizer_id != organizer.id:
            raise ValueError("Данные действия доступны только организатору игры")

        return db.query(Participant).filter(Participant.game_id == game.id).all()

    @staticmethod
    def update_participant_wishlist(
        db: Session, participant_id: int, wishlist: str
    ) -> str:
        participant = db.get(Participant, participant_id)
        if not participant:
            raise ValueError("Участник не найден")

        participant.wishlist = wishlist

        db.commit()
        db.refresh(participant)

        return "Данные успешно обновлены"

    @staticmethod
    def get_participant_by_user_id(db: Session, user_id: int) -> Participant:
        """Getting participant by user id"""
        return (
            db.query(Participant)
            .filter(Participant.user_id == user_id)
            .first_not_deleted()
        )
