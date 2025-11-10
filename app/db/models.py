from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import backref, relationship

from app.constants import GameStatus, GiftStatus, JoinRequestStatus
from app.db.database import Base


def now():
    return datetime.now(timezone.utc)


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime)

    def soft_delete(self) -> None:
        """Помечает запись в БД как удаленную"""
        if self.is_deleted:
            return

        self.is_deleted = True
        self.deleted_at = now()

        for rel in self.__mapper__.relationships:
            if rel.viewonly:
                continue

            if rel.mapper.class_ == User:
                continue

            related_value = getattr(self, rel.key)
            if not related_value:
                continue

            if isinstance(related_value, list):
                for obj in related_value:
                    if hasattr(obj, "soft_delete") and not isinstance(obj, User):
                        obj.soft_delete()
            else:
                if hasattr(related_value, "soft_delete") and not isinstance(
                    related_value, User
                ):
                    related_value.soft_delete()


class User(Base, SoftDeleteMixin):
    """Пользователь системы.

    Создаётся при регистрации. Используется как организатор, участник или админ.
    Для удаления рекомендуется использовать soft-delete (is_active=False).
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    email = Column(String(100), nullable=False)
    password_hash = Column(String(300), nullable=False)
    wishlist = Column(Text)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, onupdate=now)

    games_created = relationship(
        "Game",
        back_populates="organizer",
        cascade="save-update, merge, expunge, refresh-expire",
        passive_deletes=True,
    )
    participation = relationship(
        "Participant",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    messages_sent = relationship(
        "Message", back_populates="sender_user", foreign_keys="Message.sender_user_id"
    )
    messages_received = relationship(
        "Message",
        back_populates="receiver_user",
        foreign_keys="Message.receiver_user_id",
    )
    notifications_receiver = relationship("NotificationReceiver", back_populates="user")


class Game(Base, SoftDeleteMixin):
    """Игра (сессия Тайного Санты).

    Рекомендуется soft-delete/архивация вместо физического удаления для сохранения истории
    """

    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    budget = Column(Float)
    event_date = Column(DateTime)
    status = Column(String(20), default=GameStatus.DRAFT)
    secret_key = Column(String(10), unique=True, nullable=False)
    organizer_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False
    )
    is_private = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, onupdate=now)

    organizer = relationship("User", back_populates="games_created")
    participants = relationship(
        "Participant",
        back_populates="game",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    draws = relationship("Draw", back_populates="game", cascade="all, delete-orphan")
    gifts = relationship("Gift", back_populates="game", cascade="all, delete-orphan")


class JoinRequest(Base):
    __tablename__ = "join_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=now)
    status = Column(String(20), default=JoinRequestStatus.PENDING)
    organizer_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user = relationship("User", foreign_keys=[user_id])
    game = relationship("Game", foreign_keys=[game_id])


class Participant(Base, SoftDeleteMixin):
    """Участник конкретной игры (association User <-> Game).

    Хранит статус участия и ссылку на того, кому участник дарит подарок
    (assigned_to_id — participant.id).
    """

    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_participant_user_game"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )

    assigned_to_id = Column(Integer, ForeignKey("participants.id", ondelete="SET NULL"))

    wishlist = Column(Text)
    gift_status = Column(String(20), default=GiftStatus.NOT_SENT)
    joined_at = Column(DateTime, default=now)
    left_at = Column(DateTime)

    user = relationship("User", back_populates="participation", foreign_keys=[user_id])
    game = relationship("Game", back_populates="participants")

    assigned_to = relationship(
        "Participant",
        remote_side=[id],
        backref=backref("assigned_from", uselist=True),
        foreign_keys=[assigned_to_id],
        post_update=True,
    )

    gifts = relationship(
        "Gift",
        back_populates="participant",
        foreign_keys="[Gift.participant_id]",
        cascade="all, delete-orphan",
    )


class Draw(Base):
    """Запуск жеребьёвки (версия/сборка результатов)."""

    __tablename__ = "draws"

    id = Column(Integer, primary_key=True)
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=now)

    notification_receivers = relationship(
        "NotificationReceiver",
        secondary="notifications",
        primaryjoin="Draw.game_id==Notification.game_id",
        secondaryjoin="Notification.id==NotificationReceiver.notification_id",
        viewonly=True,
    )
    game = relationship("Game", back_populates="draws")
    assignments = relationship(
        "DrawAssignment", back_populates="draw", cascade="all, delete-orphan"
    )


class DrawAssignment(Base):
    """Результат жеребьёвки: participant_from дарит participant_to в рамках Draw."""

    __tablename__ = "draw_assignments"

    id = Column(Integer, primary_key=True)
    draw_id = Column(
        Integer, ForeignKey("draws.id", ondelete="CASCADE"), nullable=False
    )
    participant_from_id = Column(
        Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False
    )
    participant_to_id = Column(
        Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False
    )

    draw = relationship("Draw", back_populates="assignments")
    participant_from = relationship("Participant", foreign_keys=[participant_from_id])
    participant_to = relationship("Participant", foreign_keys=[participant_to_id])


class Gift(Base, SoftDeleteMixin):
    """Подарок в рамках игры."""

    __tablename__ = "gifts"

    id = Column(Integer, primary_key=True)
    participant_id = Column(
        Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False
    )
    receiver_participant_id = Column(
        Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False
    )
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )

    title = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float)
    status = Column(String(20), default=GiftStatus.PLANNED)
    sent_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now)
    is_deleted = Column(Boolean, default=False)  # soft-delete для подарка, если нужно

    participant = relationship(
        "Participant", back_populates="gifts", foreign_keys=[participant_id]
    )
    receiver_participant = relationship(
        "Participant", foreign_keys=[receiver_participant_id]
    )
    game = relationship("Game", back_populates="gifts")


class Message(Base, SoftDeleteMixin):
    """Сообщение между участниками (анонимное или нет)."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    sender_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    receiver_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    sender_participant_id = Column(
        Integer, ForeignKey("participants.id", ondelete="SET NULL"), nullable=True
    )
    receiver_participant_id = Column(
        Integer, ForeignKey("participants.id", ondelete="SET NULL"), nullable=True
    )

    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=True)

    text = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now)
    is_deleted = Column(Boolean, default=False)

    sender_user = relationship(
        "User", foreign_keys=[sender_user_id], back_populates="messages_sent"
    )
    receiver_user = relationship(
        "User", foreign_keys=[receiver_user_id], back_populates="messages_received"
    )


class Notification(Base):
    """Уведомление (сам факт события)"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now)

    receivers = relationship("NotificationReceiver", back_populates="notifications")


class NotificationReceiver(Base):
    """
    Получатель конкретного уведомления.
    Позволяет отправлять одно уведомление нескольким пользователям
    """

    __tablename__ = "notification_receiver"

    id = Column(Integer, primary_key=True)
    notification_id = Column(
        Integer, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)

    notifications = relationship("Notification", back_populates="receivers")
    user = relationship("User", back_populates="notifications_receiver")
