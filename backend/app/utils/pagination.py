from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


async def paginate(
    db: AsyncSession, stmt: Select, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE
) -> tuple[list, int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    items_stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(items_stmt)).scalars().all()
    return list(items), total
