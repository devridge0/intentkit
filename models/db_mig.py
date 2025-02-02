"""Database migration utilities."""

import logging
from typing import Callable, Type

from sqlalchemy import Column, MetaData, inspect, text
from sqlmodel import SQLModel


async def add_column_if_not_exists(engine, table_name: str, column: Column) -> None:
    """Add a column to a table if it doesn't exist.

    Args:
        engine: SQLAlchemy engine
        table_name: Name of the table
        column: Column to add
    """
    async with engine.connect() as conn:
        # Use run_sync to perform inspection on the connection
        def _get_columns(connection):
            inspector = inspect(connection)
            return [c["name"] for c in inspector.get_columns(table_name)]
        
        columns = await conn.run_sync(_get_columns)
        
        if column.name not in columns:
            async with conn.begin():
                # Build column definition
                column_def = f"{column.name} {column.type.compile(engine.dialect)}"

                # Add DEFAULT if specified
                if column.default is not None:
                    if hasattr(column.default, "arg"):
                        default_value = column.default.arg
                        if not isinstance(default_value, Callable):
                            if isinstance(default_value, bool):
                                default_value = str(default_value).lower()
                            elif isinstance(default_value, str):
                                default_value = f"'{default_value}'"
                            elif isinstance(default_value, (list, dict)):
                                default_value = "'{}'"
                            column_def += f" DEFAULT {default_value}"

                # Execute ALTER TABLE
                await conn.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
                )
                logging.info(f"Added column {column.name} to table {table_name}")


async def update_table_schema(engine, model: Type[SQLModel]) -> None:
    """Update table schema by adding missing columns from the model.

    Args:
        engine: SQLAlchemy engine
        model: SQLModel class to check for new columns
    """
    if not hasattr(model, "__table__"):
        return

    table_name = model.__tablename__
    for name, column in model.__table__.columns.items():
        if name != "id":  # Skip primary key
            await add_column_if_not_exists(engine, table_name, column)


async def safe_migrate(engine) -> None:
    """Safely migrate all SQLModel tables by adding new columns.

    Args:
        engine: SQLAlchemy engine
    """
    try:
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Get existing table metadata
        metadata = MetaData()
        async with engine.begin() as conn:
            await conn.run_sync(metadata.reflect)

        # Update schema for all SQLModel classes
        for model in SQLModel.__subclasses__():
            if hasattr(model, "__tablename__"):
                table_name = model.__tablename__
                if table_name in metadata.tables:
                    await update_table_schema(engine, model)

        logging.info("Database schema updated successfully")
    except Exception as e:
        logging.error(f"Error updating database schema: {str(e)}")
        raise
