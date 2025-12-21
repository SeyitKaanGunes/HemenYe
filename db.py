import sqlite3
from pathlib import Path
from typing import Iterable, Sequence

DB_PATH = Path(__file__).with_name("yemekye.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cuisine TEXT NOT NULL,
                description TEXT,
                min_order REAL NOT NULL,
                delivery_time TEXT NOT NULL,
                image_url TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                is_vegan INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
                user_name TEXT NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
                customer_name TEXT NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL,
                notes TEXT DEFAULT '',
                total REAL NOT NULL,
                placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                menu_item_id INTEGER NOT NULL REFERENCES menu_items(id),
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            );
            """
        )
        conn.commit()


def _insert_many(conn: sqlite3.Connection, query: str, rows: Iterable[Sequence]) -> None:
    conn.executemany(query, rows)
    conn.commit()


def seed_db() -> None:
    """Insert example data only when the database is empty."""
    with get_connection() as conn:
        has_data = conn.execute("SELECT COUNT(*) FROM restaurants;").fetchone()[0]
        if has_data:
            return

        restaurants = [
            (
                "Anadolu Sofrası",
                "Türk Mutfağı",
                "Günlük hazırlanan sulu yemekler, ızgaralar ve geleneksel tatlılar.",
                120,
                "35-45 dk",
                "https://images.unsplash.com/photo-1467003909585-2f8a72700288",
            ),
            (
                "Pide & Lahmacun Evi",
                "Antep Mutfağı",
                "Taş fırında çıtır lahmacun ve bol malzemeli pideler.",
                100,
                "25-35 dk",
                "https://images.unsplash.com/photo-1604908176868-3b6b97a4c90c",
            ),
            (
                "Sushi Nova",
                "Japon Mutfağı",
                "Roll, nigiri ve ramen seçenekleriyle modern sushi bar.",
                200,
                "45-55 dk",
                "https://images.unsplash.com/photo-1553621042-f6e147245754",
            ),
            (
                "VeganVibe",
                "Vegan",
                "Bitkisel bazlı burgerler, bowl'lar ve taze sıkım içecekler.",
                150,
                "30-40 dk",
                "https://images.unsplash.com/photo-1490645935967-10de6ba17061",
            ),
        ]

        _insert_many(
            conn,
            """
            INSERT INTO restaurants (name, cuisine, description, min_order, delivery_time, image_url)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            restaurants,
        )

        menu_items = [
            # Anadolu Sofrası
            (1, "Izgara Köfte", "Ana Yemek", 180, "Közde pişmiş köfte, domates ve biber", 0),
            (1, "Tavuk Şiş", "Ana Yemek", 170, "Yoğurtlu soslu tavuk şiş, pilav ve salata", 0),
            (1, "Fırın Sütlaç", "Tatlı", 65, "Klasik fırın sütlaç, hafif kavruk tat", 0),
            (1, "Mercimek Çorbası", "Çorba", 60, "Tereyağlı kırmızı mercimek çorbası", 0),
            # Pide & Lahmacun Evi
            (2, "Kaşarlı Pide", "Pide", 140, "Bol kaşarlı, tereyağlı pide", 0),
            (2, "Kuşbaşılı Pide", "Pide", 165, "Dana kuşbaşı, biber ve domatesli pide", 0),
            (2, "Lahmacun (2 adet)", "Lahmacun", 130, "İnce hamur, bol malzemeli lahmacun", 0),
            (2, "Ayran (Şişe)", "İçecek", 25, "Soğuk, tuzlu ayran", 0),
            # Sushi Nova
            (3, "California Roll", "Roll", 190, "Yengeç, avokado, tobiko, susam", 0),
            (3, "Spicy Salmon Roll", "Roll", 210, "Acılı somon, salatalık, nori", 0),
            (3, "Ramen", "Ana Yemek", 230, "Miso bazlı ramen, soya yumurta ve sebzeler", 0),
            (3, "Edamame", "Atıştırmalık", 95, "Deniz tuzlu haşlanmış edamame", 0),
            # VeganVibe
            (4, "Falafel Bowl", "Bowl", 175, "Humus, falafel, kinoalı sebze bowl", 1),
            (4, "Beyond Burger", "Burger", 195, "Avokado, karamelize soğan ile bitkisel burger", 1),
            (4, "Soğuk Yeşil Detoks", "İçecek", 85, "Ispanak, elma, zencefil ve limon", 1),
            (4, "Çikolatalı Chia Puding", "Tatlı", 90, "Badem sütlü chia puding, kakao ve muz", 1),
        ]

        _insert_many(
            conn,
            """
            INSERT INTO menu_items (restaurant_id, name, category, price, description, is_vegan)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            menu_items,
        )

        reviews = [
            (1, "Elif", 5, "Köfte çok lezizdi, 20 dakikada geldi."),
            (1, "Burak", 4, "Mercimek çorbasını beğendim, porsiyonlar doyurucu."),
            (2, "Gökhan", 5, "Lahmacun efsane, sıcak ve çıtır geldi."),
            (3, "Ece", 4, "Roll'lar taze, ramen biraz tuzluydu ama lezzetli."),
            (4, "Deniz", 5, "Vegan burger çok iyi, sosları harika."),
        ]

        _insert_many(
            conn,
            """
            INSERT INTO reviews (restaurant_id, user_name, rating, comment)
            VALUES (?, ?, ?, ?);
            """,
            reviews,
        )

