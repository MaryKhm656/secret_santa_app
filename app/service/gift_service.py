from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.constants import GiftStatus
from app.db.models import Game, Gift, Participant
from app.schemas.game_gift_view import GameGiftView
from app.schemas.gifts import GiftCreateData, GiftUpdateData
from app.service.game_service import GameService


class GiftService:
    @staticmethod
    def create_gift(db: Session, gift_create_data: GiftCreateData) -> Gift:
        gift = Gift(
            participant_id=gift_create_data.participant_id,
            receiver_participant_id=gift_create_data.receiver_participant_id,
            game_id=gift_create_data.game_id,
            title=gift_create_data.title,
            description=gift_create_data.description,
            price=gift_create_data.price,
            status=GiftStatus.PLANNED,
        )

        db.add(gift)
        db.commit()
        db.refresh(gift)

        return gift

    @staticmethod
    def update_gift_data(
        db: Session, new_gift_data: GiftUpdateData, gift_id: int
    ) -> Gift:
        gift = db.query(Gift).filter(Gift.id == gift_id).first_not_deleted()

        if new_gift_data.title != gift.title:
            if len(new_gift_data.title.strip()) == 0:
                raise ValueError("Слишком короткое название подарка")
            gift.title = new_gift_data.title

        if new_gift_data.description != gift.description:
            gift.description = new_gift_data.description

        if new_gift_data.price != gift.price:
            gift.price = new_gift_data.price

        db.commit()
        db.refresh(gift)

        return gift

    @staticmethod
    def update_gift_status(
        db: Session, gift_id: int, participant_id: int, new_status: str
    ) -> Gift:
        gift = (
            db.query(Gift)
            .filter(Gift.id == gift_id, Gift.participant_id == participant_id)
            .first()
        )

        if not gift:
            raise ValueError("Подарок не найден")

        if new_status not in GiftStatus.ALL:
            raise ValueError("Недопустимый статус подарка")

        gift.status = new_status

        if new_status == GiftStatus.SENT:
            gift.sent_at = datetime.now(timezone.utc)
        elif new_status == GiftStatus.RECEIVED:
            gift.received_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(gift)

        return gift

    @staticmethod
    def get_santa_gifts(db: Session, participant_id: int) -> List[Gift]:
        """Получить подарки, которые пользователь дарит (как Санта)"""
        return (
            db.query(Gift)
            .filter(Gift.participant_id == participant_id, Gift.is_deleted == False)
            .order_by(Gift.created_at.desc())
            .all()
        )

    @staticmethod
    def get_receiver_gifts(db: Session, receiver_participant_id: int) -> List[Gift]:
        """Получить подарки, которые пользователь получает"""
        return (
            db.query(Gift)
            .filter(
                Gift.receiver_participant_id == receiver_participant_id,
                Gift.is_deleted == False,
            )
            .order_by(Gift.created_at.desc())
            .all()
        )

    @staticmethod
    def get_gift_for_receiver(
        db: Session, receiver_participant_id: int
    ) -> Optional[Gift]:
        """Получить подарок для получателя (если Санта уже создал)"""
        return (
            db.query(Gift)
            .filter(
                Gift.receiver_participant_id == receiver_participant_id,
            )
            .first_not_deleted()
        )

    @staticmethod
    def get_gifts_for_user_in_game(
        db: Session, user_id: int, game: Game
    ) -> Optional[GameGiftView]:
        participation = (
            db.query(Participant)
            .filter(
                Participant.user_id == user_id,
                Participant.game_id == game.id,
                Participant.is_deleted == False,
            )
            .first()
        )

        if not participation:
            return None

        my_gift = (
            db.query(Gift)
            .filter(Gift.participant_id == participation.id, Gift.is_deleted == False)
            .first()
        )

        gift_for_me = (
            db.query(Gift)
            .filter(
                Gift.receiver_participant_id == participation.id,
                Gift.is_deleted == False,
            )
            .first()
        )

        return GameGiftView(
            game=game,
            participation=participation,
            my_gift=my_gift,
            gift_for_me=gift_for_me,
        )

    @staticmethod
    def get_user_gifts_overview(db: Session, user_id: int) -> list[GameGiftView]:
        games = GameService.get_filtered_user_games(
            db=db, user_id=user_id, role="all", game_status="all"
        )

        result = []
        for game in games:
            view = GiftService.get_gifts_for_user_in_game(db, user_id, game)
            if view:
                result.append(view)

        return result

    @staticmethod
    def get_gift_by_id(db: Session, gift_id: int) -> Gift:
        return db.query(Gift).filter(Gift.id == gift_id).first_not_deleted()

    @staticmethod
    def delete_gift(db: Session, gift_id: int) -> Optional[str]:
        gift = db.query(Gift).filter(Gift.id == gift_id).first_not_deleted()
        gift.soft_delete()
        db.commit()

        return "Подарок удален"
