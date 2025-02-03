"""Add referrals column

Revision ID: 5086e79bba88
Revises: 
Create Date: 2025-01-26 13:58:58.387458

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5086e79bba88'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('submission')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('referrals', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('referrals')

    op.create_table('submission',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('custom_link', sa.VARCHAR(length=200), nullable=True),
    sa.Column('name', sa.VARCHAR(length=100), nullable=True),
    sa.Column('email', sa.VARCHAR(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
