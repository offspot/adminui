import datetime
import uuid
from uuid import UUID

from pydantic.main import BaseModel

from adminui.constants import DEFAULT_SESSION_DURATION_MN
from adminui.utils import get_now


class Session(BaseModel):
    id: UUID
    expire_on: datetime.datetime

    @property
    def is_valid(self) -> bool:
        return self.expire_on > get_now()


class SessionManager:
    def __init__(
        self,
        default_expiry: datetime.timedelta = datetime.timedelta(
            minutes=DEFAULT_SESSION_DURATION_MN
        ),
    ):
        self.default_expiry = default_expiry
        self.sessions: dict[str, Session] = {}

    def create(self, expiry: datetime.timedelta | None = None) -> Session:
        self.cleanup()
        session = Session(
            id=uuid.uuid4(), expire_on=get_now() + (expiry or self.default_expiry)
        )
        self.sessions[str(session.id)] = session
        return session

    def get(self, session_id: str | UUID) -> Session | None:
        self.cleanup()
        return self.sessions.get(str(session_id))

    def remove(self, session_id: str | UUID) -> None:
        try:
            del self.sessions[str(session_id)]
        except KeyError:
            pass

    def cleanup(self):
        for session in list(self.sessions.values()):
            if not session.is_valid:
                self.remove(session.id)


session_manager = SessionManager()
