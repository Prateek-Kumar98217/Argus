#Models to map database tables to python objects


from uuid import UUID, uuid4
from pgvector import Vector
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Text, String, DateTime, ForeignKey, UniqueConstraint

class Base(DeclarativeBase):
    pass

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    source_chunk_id: Mapped[UUID] = mapped_column(ForeignKey('chunks.id'))

class Edge(Base):
    __tablename__ = "edges"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_node_id: Mapped[UUID] = mapped_column(ForeignKey('nodes.id'), ondelete="CASCADE")
    target_node_id: Mapped[UUID] = mapped_column(ForeignKey('nodes.id'), ondelete="CASCADE")
    realationship_type: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    source_node_id: Mapped[UUID] = mapped_column(ForeignKey('chunks.id'), ondelete="CASCADE")

    __table_args__ = (
        UniqueConstraint('source_node_id', 'target_node_id', 'relationship_type', name="unique_source_target_rel")
    )
