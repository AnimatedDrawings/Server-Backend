"""change type id in AD_model

Revision ID: 5228551c642e
Revises: f5e4b1c949a5
Create Date: 2023-07-17 08:33:03.537418

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5228551c642e'
down_revision = 'f5e4b1c949a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('AnimatedDrawings', 'id', type_=sa.String, existing_type=sa.Integer)

def downgrade() -> None:
    pass
