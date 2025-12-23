# app/pagination.py - simple query pagination helper
def paginate(query, page: int, per_page: int):
    if page < 1:
        page = 1
    total = query.count()
    pages = max(1, (total + per_page - 1) // per_page) if total else 1
    if page > pages:
        page = pages
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    return items, page, pages, total
