"""Initial Phase 11 portable schema."""
from alembic import op
from core.persistence.database import Base
from core.persistence import models
revision="0001_initial";down_revision=None;branch_labels=None;depends_on=None
def upgrade(): Base.metadata.create_all(op.get_bind())
def downgrade(): Base.metadata.drop_all(op.get_bind())
