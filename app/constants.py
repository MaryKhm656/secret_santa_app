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
    ALL = [PLANNED, NOT_SENT, SENT, RECEIVED]


class JoinRequestStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ALL = [PENDING, APPROVED, REJECTED]


class NotificationsData:
    NEW_JOIN_REQUEST = "У вас новый запрос на вступление в игру! Проверьте запросы."
    NEW_PARTICIPANT_IN_GAME = "Новый пользователь в вашей игре!"
    ACCEPT_JOIN_REQUEST = (
        "Вы в игре!\n"
        "Организатор принял ваш запрос и теперь вы "
        "можете участвовать в игре Тайного Санты!"
    )
    DRAW_IS_COMPLETED = (
        "Жеребьевка завершена!\nЗагляни в личный кабинет и узнай своего получателя."
    )
