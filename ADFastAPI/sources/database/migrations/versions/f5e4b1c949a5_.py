"""empty message

Revision ID: f5e4b1c949a5
Revises: 71ea19b718f7
Create Date: 2023-07-16 13:20:47.834528

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5e4b1c949a5'
down_revision = '71ea19b718f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.alter_column('Animated_Drawings', 'id', type_=sa.Integer, existing_type=sa.String)
    # op.drop_column('Animated_Drawings', 'id')
    # op.add_column('Animated_Drawings', sa.Column('id', sa.String()))
    # op.create_primary_key(None, 'Animated_Drawings', ['id'])
    # ### end Alembic commands ###
    pass


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###