
import sqlite3

def check_lengths():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    print("Checking max lengths for item_estoque columns...")
    
    columns = ['codigo', 'codigo_opcional', 'tipo', 'dimensao', 'un', 'descricao']
    
    for col in columns:
        cursor.execute(f"SELECT MAX(length({col})) FROM item_estoque")
        max_len = cursor.fetchone()[0]
        print(f"Max length for {col}: {max_len}")
        
        if max_len and max_len > 50:
            print(f"⚠️  WARNING: {col} has values longer than 50 chars!")
            cursor.execute(f"SELECT id, {col} FROM item_estoque WHERE length({col}) > 50 LIMIT 3")
            for row in cursor.fetchall():
                print(f"   - ID {row[0]}: {row[1]}")

    conn.close()

if __name__ == "__main__":
    check_lengths()
