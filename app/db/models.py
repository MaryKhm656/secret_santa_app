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
        """Marks a record in the database as deleted"""
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
    """System user - can be organizer or participant"""

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
    notifications_receiver = relationship("NotificationReceiver", back_populates="user")


class Game(Base, SoftDeleteMixin):
    """Secret Santa game session"""

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
    join_requests = relationship(
        "JoinRequest",
        back_populates="game",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class JoinRequest(Base, SoftDeleteMixin):
    """User request to join a game"""

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
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)

    user = relationship("User", foreign_keys=[user_id])
    game = relationship("Game", back_populates="join_requests", foreign_keys=[game_id])


class Participant(Base, SoftDeleteMixin):
    """User participation in a specific game"""

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
    """Draw execution instance with results"""

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
    """Draw result: who gives gift to whom"""

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
    """Gift within a game"""

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


class Notification(Base):
    """Notification event"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=now)

    receivers = relationship("NotificationReceiver", back_populates="notifications")


class NotificationReceiver(Base):
    """Notification recipient linking user to notification"""

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
