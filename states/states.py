from aiogram.fsm.state import State, StatesGroup

class RecordStates(StatesGroup):
    """Состояния для записи времени потока и спринта."""
    waiting_for_flow_duration = State()
    waiting_for_sprint_duration = State()
    flow_active = State()
    flow_paused = State()
