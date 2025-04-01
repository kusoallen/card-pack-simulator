import sqlite3

# 建立資料庫檔案（會自動產生 draw_card.db）
conn = sqlite3.connect("draw_card.db")
c = conn.cursor()

# 建立抽卡紀錄表
c.execute('''
    CREATE TABLE IF NOT EXISTS draw_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        card_name TEXT,
        rarity TEXT,
        draw_time TEXT
    )
''')

# 建立學生保底狀態表
c.execute('''
    CREATE TABLE IF NOT EXISTS student_status (
        student_id TEXT PRIMARY KEY,
        total_draws INTEGER DEFAULT 0,
        no_legendary_count INTEGER DEFAULT 0
    )
''')

conn.commit()
conn.close()

print("✅ SQLite 資料庫建立完成（draw_card.db）！")
