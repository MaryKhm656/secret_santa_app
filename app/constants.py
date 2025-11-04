class GameStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ALL = [DRAFT, ACTIVE, COMPLETED]


class GiftStatus:
    PLANNED = "planned"
    NOT_SENT = "not_sent"
    SENT = "sent"
    RECEIVED = "received"


class DrawStatus:
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"


class JoinRequestStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ALL = [PENDING, APPROVED, REJECTED]


class NotificationsData:
    JOIN_REQUEST_HAS_BEEN_SEND = (
        "Запрос на вступление в игру успешно отправлен!\n"
        "Мы пришлем уведомление о решении организатора игры"
    )
    NEW_JOIN_REQUEST = "У вас новый запрос на вступление в игру! Проверьте запросы."
    NEW_PARTICIPANT_IN_GAME = "Новый пользователь в вашей игре!"
    ACCEPT_JOIN_REQUEST = (
        "Вы в игре!\n"
        "Организатор принял ваш запрос и теперь вы "
        "можете участвовать в игре Тайного Санты!"
    )
