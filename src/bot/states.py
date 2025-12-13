"""FSM states for bot conversations."""

from aiogram.fsm.state import State, StatesGroup


class AddExpenseStates(StatesGroup):
    """States for structured /add command flow."""

    category = State()  # Waiting for category selection
    amount = State()  # Waiting for amount input
    description = State()  # Waiting for description (optional)
