"""Add conversations and CV attachment metadata.

Revision ID: 72e4c11a9f02
Revises: 193591bf4d83
"""
from alembic import op
import sqlalchemy as sa

revision = "72e4c11a9f02"
down_revision = "193591bf4d83"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("agent_applications") as batch:
        batch.add_column(sa.Column("cv_storage_name", sa.String(255), nullable=True))
        batch.add_column(sa.Column("cv_original_name", sa.String(255), nullable=True))
        batch.add_column(sa.Column("cv_mime_type", sa.String(100), nullable=True))
    op.create_table("conversations", sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("agent_id", sa.Integer(), nullable=False), sa.Column("property_id", sa.Integer(), nullable=False), sa.Column("id", sa.Integer(), primary_key=True), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["agent_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id", "agent_id", "property_id"))
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"]); op.create_index("ix_conversations_agent_id", "conversations", ["agent_id"]); op.create_index("ix_conversations_property_id", "conversations", ["property_id"]); op.create_index("ix_conversations_created_at", "conversations", ["created_at"])
    op.create_table("conversation_messages", sa.Column("conversation_id", sa.Integer(), nullable=False), sa.Column("sender_id", sa.Integer(), nullable=False), sa.Column("body", sa.Text(), nullable=False), sa.Column("is_read", sa.Boolean(), nullable=False), sa.Column("id", sa.Integer(), primary_key=True), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"))
    for name, cols in (("ix_conversation_messages_conversation_id", ["conversation_id"]), ("ix_conversation_messages_sender_id", ["sender_id"]), ("ix_conversation_messages_is_read", ["is_read"]), ("ix_conversation_messages_created_at", ["created_at"])): op.create_index(name, "conversation_messages", cols)


def downgrade():
    op.drop_table("conversation_messages"); op.drop_table("conversations")
    with op.batch_alter_table("agent_applications") as batch:
        batch.drop_column("cv_mime_type"); batch.drop_column("cv_original_name"); batch.drop_column("cv_storage_name")
