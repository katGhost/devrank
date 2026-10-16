"""add scaffold fields to project

Revision ID: c4d8e1a9f3b2
Revises: 9a3f2c7d5e4b
Create Date: 2026-10-16 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d8e1a9f3b2'
down_revision = '9a3f2c7d5e4b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tech_stack', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('github_repo_url', sa.String(length=512), nullable=True))


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('github_repo_url')
        batch_op.drop_column('tech_stack')
