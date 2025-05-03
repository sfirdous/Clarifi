from sqlalchemy import Table, Column ,String
from .database import metadata

users = Table(
    "users",
    metadata,
    Column("user_id",String,primary_key=True),
    Column("username",String,unique=True),
    Column("email",String,unique=True),
    Column("password",String),
    Column("bank_name",String),
)

# pdfs = Table(
#     "pdfs",
#     metadata,
#     Column("id", Integer, primary_key=True),
#     Column("filename", String),
#     Column("upload_time", DateTime, default=func.now())
# )

# tables = Table(
#     "tables",
#     metadata,
#     Column("id", Integer, primary_key=True),
#     Column("pdf_id", Integer, ForeignKey("pdfs.id")),
#     Column("page_number", Integer),
#     Column("row_number", Integer),
#     Column("col_1", Text),
#     Column("col_2", Text),
#     Column("col_3", Text),
#     Column("col_4", Text),
#     Column("col_5", Text)
# )


# budgets = Table(
#     "budgets",
#     metadata,
#     Column("pdf_id", String, primary_key=True),
#     Column("month", String, primary_key=True),  # Format: YYYY-MM
#     Column("budget_amount", Float),
# )
