#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para criar um usuário admin no banco de dados"""

from app import app, db, User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def criar_admin():
    """Cria um usuário admin no banco de dados"""
    with app.app_context():
        # Verificar se já existe um admin
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print(f"✅ Usuário admin já existe no banco de dados")
            print(f"   Username: {admin.username}")
            print(f"   Role: {admin.role}")
        else:
            print("📝 Criando usuário admin...")
            hashed_password = bcrypt.generate_password_hash('admin').decode('utf-8')
            admin_user = User(username='admin', password_hash=hashed_password, role='admin')
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Usuário 'admin' criado com sucesso!")
            print("   Username: admin")
            print("   Password: admin")
            print("   Role: admin")
            print("\n🔓 Você agora pode fazer login com essas credenciais!")

if __name__ == '__main__':
    criar_admin()
