#Models to map database tables to python objects


from uuid import UUID, uuid4
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector
from sqlalchemy import Text, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class Base(DeclarativeBase):
    pass

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_chunk_id: Mapped[UUID] = mapped_column(
        ForeignKey('chunks.id', ondelete="SET NULL"), 
        nullable=True
    )

class Edge(Base):
    __tablename__ = "edges"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_node_id: Mapped[UUID] = mapped_column(
        ForeignKey('nodes.id', ondelete="CASCADE"), 
        nullable=False
    )
    target_node_id: Mapped[UUID] = mapped_column(
        ForeignKey('nodes.id', ondelete="CASCADE"), 
        nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "source_node_id", "target_node_id", "relationship_type",
            name="unique_source_target_rel",
        ),
    )
