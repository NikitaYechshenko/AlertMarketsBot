from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String, index=True, nullable=False)
    direction = Column(String, nullable=False)  # ABOVE or BELOW
    target_price = Column(Numeric(precision=18, scale=8), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    exchange = Column(String, nullable=False) # Добавляем поле для хранения информации о бирже, на которой установлен алерт
    user = relationship("User", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert id={self.id} symbol={self.symbol} target={self.target_price}>"
