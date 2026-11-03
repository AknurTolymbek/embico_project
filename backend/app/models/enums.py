"""
Enum типы для моделей базы данных.
Все значения на английском, перевод на фронтенде.
"""
import enum


class UserRole(str, enum.Enum):
    """Роли пользователей в системе"""
    REPRODUCTOLOGIST = "reproductologist"  # Репродуктолог
    EMBRYOLOGIST = "embryologist"          # Эмбриолог


class CycleStatus(str, enum.Enum):
    """Статусы цикла ЭКО"""
    ACTIVE = "active"          # Активен
    COMPLETED = "completed"    # Завершён
    CANCELLED = "cancelled"    # Отменён


class CycleStage(str, enum.Enum):
    """Этапы клинического пути цикла ЭКО"""
    PREPARATION = "preparation"    # Подготовка
    STIMULATION = "stimulation"    # Стимуляция
    RETRIEVAL = "retrieval"        # Пункция (забор ооцитов)
    EMBRYOLOGY = "embryology"      # Эмбриология (оплодотворение, культивирование)
    TRANSFER = "transfer"          # Перенос эмбрионов
    OUTCOME = "outcome"            # Исход