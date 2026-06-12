"""add service catalog and business services

Revision ID: 938890c58dbc
Revises: 7b14ac101df4
Create Date: 2026-06-12 23:16:55.218976
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = "938890c58dbc"
down_revision = '7b14ac101df4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_services_name"),
    )
    op.create_index("ix_services_id", "services", ["id"], unique=False)

    op.create_table(
        "business_services",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("minimum_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "minimum_price > 0",
            name="ck_business_services_minimum_price_positive",
        ),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_id",
            "service_id",
            name="uq_business_services_business_service",
        ),
    )
    op.create_index("ix_business_services_id", "business_services", ["id"], unique=False)
    op.create_index(
        "ix_business_services_business_active",
        "business_services",
        ["business_id", "is_active"],
        unique=False,
    )
    op.create_index(
        "ix_business_services_service_active",
        "business_services",
        ["service_id", "is_active"],
        unique=False,
    )

    services_table = sa.table(
        "services",
        sa.column("name", sa.String(length=255)),
        sa.column("description", sa.String(length=1000)),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )

    now = datetime.utcnow()
    op.bulk_insert(
        services_table,
        [
            {
                "name": "Yağ Değişimi",
                "description": "Motor yağının ve yağ filtresinin yenilenmesi.",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "Fren Bakımı",
                "description": "Fren balata, disk ve hidrolik kontrolü.",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "Şanzıman Bakımı",
                "description": "Şanzıman yağı ve bağlantı elemanlarının kontrolü.",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "Lastik Değişimi",
                "description": "Lastik sökme, takma ve balans işlemleri.",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "Motor Arıza Tespiti",
                "description": "Arıza kodu okuma ve temel motor diagnostik kontrolü.",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "Periyodik Bakım",
                "description": "Üretici bakım planına uygun genel araç kontrolü.",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        ],
    )


def downgrade():
    op.drop_index("ix_business_services_service_active", table_name="business_services")
    op.drop_index("ix_business_services_business_active", table_name="business_services")
    op.drop_index("ix_business_services_id", table_name="business_services")
    op.drop_table("business_services")

    op.drop_index("ix_services_id", table_name="services")
    op.drop_table("services")
